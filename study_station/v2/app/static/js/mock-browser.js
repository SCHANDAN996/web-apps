/* Filter existing cards locally. No question requests or per-exam queries. */
(function(){
  'use strict';
  function init(){
    var root=document.querySelector('[data-mock-browser]');if(!root||root.dataset.wired)return;root.dataset.wired='1';
    var input=root.querySelector('[data-mock-search]'),body='';
    function filter(){
      var query=input.value.trim().toLocaleLowerCase(),visible=0;
      document.querySelectorAll('[data-mock-card]').forEach(function(card){card.hidden=!!((body&&card.dataset.mockBody!==body)||(query&&card.dataset.mockName.toLocaleLowerCase().indexOf(query)<0));if(!card.hidden)visible++;});
      document.querySelectorAll('[data-mock-group]').forEach(function(group){group.hidden=!group.querySelector('[data-mock-card]:not([hidden])');});
      var empty=document.querySelector('[data-mock-empty]');if(empty)empty.hidden=visible>0;
    }
    input.addEventListener('input',filter);
    root.querySelectorAll('[data-mock-filter]').forEach(function(button){button.addEventListener('click',function(){body=button.dataset.mockFilter;root.querySelectorAll('[data-mock-filter]').forEach(function(b){b.setAttribute('aria-pressed',String(b===button));});filter();});});
  }
  window.SSMockBrowser={init:init};
})();
