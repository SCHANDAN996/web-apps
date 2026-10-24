package com.studystation.app

import android.app.Activity
import android.net.Uri
import android.webkit.WebView
import androidx.webkit.WebMessageCompat
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import com.android.billingclient.api.*
import org.json.JSONArray
import org.json.JSONObject

/** Play owns checkout; the backend alone verifies and acknowledges before granting access. */
class PlayBillingBridge(private val activity: Activity, private val web: WebView) {
    private val origin=Uri.parse(BuildConfig.BASE_URL).let { "${it.scheme}://${it.authority}" }
    private var generation=0
    private var dead=false
    private var account=""
    private var configuredPlans=emptyList<PlayBillingPolicy.Plan>()
    private var finishPurchase: ((JSONObject)->Unit)?=null
    private var connecting=false
    private val connectWaiters=mutableListOf<(Boolean)->Unit>()
    private var choiceConfigured=false
    private var clientGeneration=0
    private data class ChoiceContext(val epoch:Int,val account:String,val plan:PlayBillingPolicy.Plan,val offer:String,val country:String)
    private var choiceContext:ChoiceContext?=null
    private var client=buildClient(false)
    private fun buildClient(choice:Boolean):BillingClient {
        val clientEpoch=++clientGeneration
        val builder=BillingClient.newBuilder(activity)
        .setListener { result,purchases ->
            if(clientEpoch!=clientGeneration || dead)return@setListener
            val finish=finishPurchase;finishPurchase=null;choiceContext=null
            if(finish!=null) finish(purchaseResult(result,purchases ?: emptyList()))
            // An interrupted page can recover these through restore; no tokens go to another page.
        }
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().enablePrepaidPlans().build())
        .enableAutoServiceReconnection()
        if(choice)builder.enableUserChoiceBilling { details ->
            activity.runOnUiThread {
                if(clientEpoch!=clientGeneration || dead)return@runOnUiThread
                val context=choiceContext;choiceContext=null
                val finish=finishPurchase;finishPurchase=null
                if(context==null || finish==null || dead || !PlayUserChoicePolicy.sameFlow(clientEpoch,clientGeneration,context.epoch,generation,context.account,account))return@runOnUiThread
                val products=details.products
                val valid=PlayUserChoicePolicy.callbackAllowed(choiceConfigured,context.country,details.externalTransactionToken,
                    products.map { Triple(it.id,it.type,it.offerToken ?: "") },context.plan.product,context.offer)
                if(!valid){finish(error("unavailable"));return@runOnUiThread}
                finish(JSONObject().put("ok",true).put("alternative",JSONObject()
                    .put("external_transaction_token",details.externalTransactionToken)
                    .put("plan_id",context.plan.id).put("product_id",context.plan.product)
                    .put("base_plan_id",context.plan.base).put("country_code",context.country)))
            }
        }
        return builder.build()
    }
    /** Query Play country for every flow; never infer it from locale, SIM, IP or a cached value. */
    private fun retireClient(choice:Boolean=false) {
        clientGeneration++ // Fence callbacks before ending the previous connection.
        client.endConnection();connecting=false;connectWaiters.clear()
        client=buildClient(choice)
    }
    private fun prepareChoice(current:()->Boolean,done:(Boolean,String)->Unit) {
        val clientEpoch=clientGeneration
        client.getBillingConfigAsync(GetBillingConfigParams.newBuilder().build()) { result,config ->
            activity.runOnUiThread {
                if(dead || clientEpoch!=clientGeneration || !current())return@runOnUiThread
                val country=if(result.responseCode==BillingClient.BillingResponseCode.OK)config?.countryCode ?: "" else ""
                val choice=PlayUserChoicePolicy.eligible(choiceConfigured,country)
                // One SDK client per purchase prevents a late old-flow callback from
                // consuming a subsequent flow's completion, even for the same product.
                retireClient(choice)
                connect {done(it,country)}
            }
        }
    }
    private val script="""
      (function(){if(window!==window.top||!window.SSPlayBillingNative||window.StudyStationBilling)return;
      var seq=0,pending={};function request(op,value){if(op==='purchase'&&(!navigator.userActivation||!navigator.userActivation.isActive))return Promise.resolve({ok:false,error:'gesture_required'});
      return new Promise(function(resolve){var id=String(++seq);pending[id]=resolve;window.SSPlayBillingNative.postMessage(JSON.stringify({op:op,value:value||null,requestId:id}));
      setTimeout(function(){if(pending[id]){delete pending[id];resolve({ok:false,error:'unavailable'});}},op==='purchase'?180000:30000);});}
      window.SSPlayBillingNative.onmessage=function(e){try{var result=JSON.parse(e.data),fn=pending[result.requestId];if(fn){delete pending[result.requestId];delete result.requestId;fn(result);}}catch(ignore){}};
      Object.defineProperty(window,'StudyStationBilling',{value:Object.freeze({query:function(config){return request('query',config);},purchase:function(plan){return request('purchase',plan);},restore:function(){return request('restore');}})});
      window.dispatchEvent(new Event('ss-play-billing-ready'));})();
    """.trimIndent()
    private fun error(code: String)=JSONObject().put("ok",false).put("error",code)
    private fun connect(done:(Boolean)->Unit) {
        if(dead){done(false);return}
        if(client.isReady){done(true);return}
        connectWaiters.add(done)
        if(connecting)return
        connecting=true
        val clientEpoch=clientGeneration
        client.startConnection(object:BillingClientStateListener {
            override fun onBillingSetupFinished(result:BillingResult) {
                if(clientEpoch!=clientGeneration || dead)return
                connecting=false;val waiters=connectWaiters.toList();connectWaiters.clear()
                waiters.forEach { it(!dead && result.responseCode==BillingClient.BillingResponseCode.OK) }
            }
            override fun onBillingServiceDisconnected() { }
        })
    }
    private fun purchases(rows:List<Purchase>)=JSONArray().also { output ->
        rows.filter { p -> p.products.any { product -> PlayBillingPolicy.plans.any { it.product==product } } }.take(20).forEach { p ->
            if(p.purchaseToken.length in 16..16384) output.put(JSONObject().put("purchaseToken",p.purchaseToken).put("state",if(p.purchaseState==Purchase.PurchaseState.PURCHASED)"purchased" else "pending"))
        }
    }
    private fun purchaseResult(result:BillingResult,rows:List<Purchase>):JSONObject = when(result.responseCode) {
        BillingClient.BillingResponseCode.OK -> JSONObject().put("ok",true).put("purchases",purchases(rows))
        BillingClient.BillingResponseCode.USER_CANCELED -> error("cancelled")
        BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED -> error("already_owned")
        else -> error("unavailable")
    }
    private fun queryPlans(done:(List<ProductDetails>)->Unit) {
        if(dead || configuredPlans.isEmpty()){done(emptyList());return}
        val list=configuredPlans.map { QueryProductDetailsParams.Product.newBuilder().setProductId(it.product).setProductType(BillingClient.ProductType.SUBS).build() }
        client.queryProductDetailsAsync(QueryProductDetailsParams.newBuilder().setProductList(list).build()) { result,details ->
            activity.runOnUiThread {done(if(result.responseCode==BillingClient.BillingResponseCode.OK)details.productDetailsList else emptyList())}
        }
    }
    private fun offer(details:ProductDetails,plan:PlayBillingPolicy.Plan)=details.subscriptionOfferDetails?.firstOrNull { o ->
        o.basePlanId==plan.base && PlayBillingPolicy.prepaid(o.basePlanId,o.offerId,o.pricingPhases.pricingPhaseList.map { it.billingPeriod to it.recurrenceMode })
    }
    fun install() {
        if(!WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER))return
        WebViewCompat.addWebMessageListener(web,"SSPlayBillingNative",setOf(origin)) { _,message,source,top,reply ->
            if(dead || message.type!=WebMessageCompat.TYPE_STRING || !GoogleAuthPolicy.allowed(source.toString(),web.url,BuildConfig.BASE_URL,top))return@addWebMessageListener
            val data=runCatching {val raw=message.data ?: kotlin.error("invalid");require(raw.length<=8192);JSONObject(raw).also {require(it.keys().asSequence().toSet()==setOf("op","value","requestId"));require(Regex("[0-9]{1,12}").matches(it.getString("requestId")))}}.getOrNull() ?: return@addWebMessageListener
            val epoch=generation;val request=data.getString("requestId")
            fun send(result:JSONObject) {if(!dead && epoch==generation && GoogleAuthPolicy.allowed(source.toString(),web.url,BuildConfig.BASE_URL,top))runCatching {reply.postMessage(result.put("requestId",request).toString())}}
            when(data.optString("op")) {
                "query" -> {
                    if(finishPurchase!=null){send(error("busy"));return@addWebMessageListener}
                    val config=runCatching {
                        val c=data.getJSONObject("value");require(c.getBoolean("enabled") && c.getString("package_name")=="com.studystation.app")
                        val id=c.getString("obfuscated_account_id");require(PlayBillingPolicy.validAccount(id))
                        val rows=c.getJSONArray("products");require(rows.length() in 1..2)
                        val plans=(0 until rows.length()).map {val p=rows.getJSONObject(it);PlayBillingPolicy.Plan(p.getString("plan_id"),p.getString("product_id"),p.getString("base_plan_id")).also {require(PlayBillingPolicy.allowed(it.id,it.product,it.base))}}
                        require(plans.map { it.id }.distinct().size==plans.size)
                        val choice=c.optJSONObject("user_choice")
                        val countries=choice?.optJSONArray("countries")
                        val allowed=choice?.opt("enabled")==true && countries!=null && countries.length()==1 && countries.optString(0)=="IN"
                        Triple(id,plans,allowed)
                    }.getOrNull()
                    if(config==null){account="";configuredPlans=emptyList();choiceConfigured=false;send(error("configuration"));return@addWebMessageListener}
                    if(account.isNotEmpty() && account!=config.first)retireClient()
                    account=config.first;configuredPlans=config.second;choiceConfigured=config.third
                    connect { connected -> if(!connected)send(error("unavailable")) else queryPlans { details ->
                        val rows=JSONArray()
                        configuredPlans.forEach { plan -> details.firstOrNull { it.productId==plan.product }?.let { detail -> offer(detail,plan)?.let { o ->
                            val phase=o.pricingPhases.pricingPhaseList.single()
                            rows.put(JSONObject().put("plan_id",plan.id).put("product_id",plan.product).put("price",phase.formattedPrice).put("billing_period",phase.billingPeriod))
                        }}}
                        send(JSONObject().put("ok",true).put("products",rows))
                    }}
                }
                "purchase" -> {
                    if(finishPurchase!=null){send(error("busy"));return@addWebMessageListener}
                    val plan=configuredPlans.firstOrNull {it.id==data.optString("value")}
                    if(plan==null || !PlayBillingPolicy.validAccount(account)){send(error("configuration"));return@addWebMessageListener}
                    val purchaseAccount=account
                    // Retire the last flow before installing this request's completion.
                    retireClient()
                    val completion:(JSONObject)->Unit={send(it)}
                    finishPurchase=completion
                    web.postDelayed({
                        if(finishPurchase===completion){finishPurchase=null;choiceContext=null;retireClient();send(error("unavailable"))}
                    },180000L)
                    web.evaluateJavascript("Boolean(navigator.userActivation&&navigator.userActivation.isActive)") { active ->
                        if(finishPurchase!==completion)return@evaluateJavascript
                        if(active!="true" || epoch!=generation){finishPurchase=null;send(error("gesture_required"));return@evaluateJavascript}
                        connect { connected ->
                            if(finishPurchase!==completion)return@connect
                            if(!connected || dead || epoch!=generation){finishPurchase=null;send(error("unavailable"))}
                            else prepareChoice({!dead && epoch==generation && account==purchaseAccount && finishPurchase===completion}) { ready,country ->
                              if(finishPurchase!==completion)return@prepareChoice
                              if(!ready || dead || epoch!=generation || account!=purchaseAccount){finishPurchase=null;send(error("unavailable"));return@prepareChoice}
                              queryPlans { details ->
                                if(finishPurchase!==completion)return@queryPlans
                                if(dead || epoch!=generation || account!=purchaseAccount){finishPurchase=null;return@queryPlans}
                                val detail=details.firstOrNull {it.productId==plan.product};val selected=detail?.let {offer(it,plan)}
                                if(detail==null || selected==null){finishPurchase=null;send(error("unavailable"));return@queryPlans}
                                val product=BillingFlowParams.ProductDetailsParams.newBuilder().setProductDetails(detail).setOfferToken(selected.offerToken).build()
                                choiceContext=ChoiceContext(epoch,purchaseAccount,plan,selected.offerToken,country)
                                val result=client.launchBillingFlow(activity,BillingFlowParams.newBuilder().setProductDetailsParamsList(listOf(product)).setObfuscatedAccountId(purchaseAccount).build())
                                if(result.responseCode!=BillingClient.BillingResponseCode.OK){finishPurchase=null;choiceContext=null;send(purchaseResult(result,emptyList()))}
                              }
                            }
                        }
                    }
                }
                "restore" -> connect { connected ->
                    if(!connected)send(error("unavailable")) else client.queryPurchasesAsync(QueryPurchasesParams.newBuilder().setProductType(BillingClient.ProductType.SUBS).build()) { result,rows -> activity.runOnUiThread { send(purchaseResult(result,rows)) } }
                }
                else -> send(error("configuration"))
            }
        }
        if(WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT))WebViewCompat.addDocumentStartJavaScript(web,script,setOf(origin))
    }
    fun pageStarted(){generation++;account="";configuredPlans=emptyList();choiceConfigured=false;choiceContext=null;finishPurchase=null;retireClient()}
    fun pageFinished(){if(!dead && GoogleAuthPolicy.allowed(origin,web.url,BuildConfig.BASE_URL,true)&&WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER))web.evaluateJavascript(script,null)}
    fun destroy(){dead=true;generation++;clientGeneration++;finishPurchase=null;choiceContext=null;connectWaiters.clear();client.endConnection()}
}
