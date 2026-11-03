(function(){'use strict';
// Paper and ink are separate so an eraser never punches holes in the page.
const layers=new WeakMap();
function drawStroke(ctx,s,w,h){
 const points=s.points||[];if(!points.length)return;
 ctx.save();ctx.globalCompositeOperation=s.tool==='erase'?'destination-out':'source-over';
 ctx.globalAlpha=s.tool==='erase'?1:(s.opacity===undefined?(s.tool==='highlighter'?.25:1):s.opacity);
 ctx.lineWidth=s.width;ctx.strokeStyle=ctx.fillStyle=s.color;ctx.lineCap=ctx.lineJoin='round';ctx.beginPath();
 const a=points[0],b=points[points.length-1];
 if(s.tool==='rect')ctx.rect(a[0]*w,a[1]*h,(b[0]-a[0])*w,(b[1]-a[1])*h);
 else if(s.tool==='circle')ctx.ellipse((a[0]+b[0])*w/2,(a[1]+b[1])*h/2,Math.abs(b[0]-a[0])*w/2,Math.abs(b[1]-a[1])*h/2,0,0,Math.PI*2);
 else if(points.length===1){ctx.arc(a[0]*w,a[1]*h,s.width/2,0,Math.PI*2);ctx.fill();ctx.restore();return;}
 else if(s.tool==='line'){ctx.moveTo(a[0]*w,a[1]*h);ctx.lineTo(b[0]*w,b[1]*h);}
 else points.forEach((p,i)=>i?ctx.lineTo(p[0]*w,p[1]*h):ctx.moveTo(p[0]*w,p[1]*h));
 ctx.stroke();ctx.restore();
}
function paper(ctx,type,w,h){ctx.fillStyle='#ffffff';ctx.fillRect(0,0,w,h);if(type==='blank')return;ctx.save();ctx.strokeStyle='#dce3ec';ctx.lineWidth=1;ctx.beginPath();for(let y=32;y<h;y+=32){ctx.moveTo(0,y+.5);ctx.lineTo(w,y+.5);}if(type==='grid')for(let x=32;x<w;x+=32){ctx.moveTo(x+.5,0);ctx.lineTo(x+.5,h);}ctx.stroke();ctx.restore();}
function paint(canvas,page,preview){
 const w=canvas.width,h=canvas.height,strokes=page.strokes||[];
 let cache=layers.get(canvas);if(!cache||cache.w!==w||cache.h!==h){cache={w,h,ink:document.createElement('canvas'),preview:document.createElement('canvas'),items:[]};for(const c of [cache.ink,cache.preview]){c.width=w;c.height=h;}layers.set(canvas,cache);}
 // Append-only strokes reuse committed ink; undo, replacement and edits rebuild.
 let start=cache.items.length;const append=start<=strokes.length&&cache.items.every((s,i)=>s===strokes[i]);
 const ink=cache.ink.getContext('2d');if(!append){ink.clearRect(0,0,w,h);start=0;}
 for(let i=start;i<strokes.length;i++)drawStroke(ink,strokes[i],w,h);cache.items=strokes.slice();
 const ctx=canvas.getContext('2d');ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.clearRect(0,0,w,h);paper(ctx,page.paper||'blank',w,h);
 if(preview){const p=cache.preview.getContext('2d');p.clearRect(0,0,w,h);p.drawImage(cache.ink,0,0);drawStroke(p,preview,w,h);ctx.drawImage(cache.preview,0,0);}else ctx.drawImage(cache.ink,0,0);ctx.restore();
}
window.SSWorkspaceRender={drawStroke,paint,invalidate:canvas=>layers.delete(canvas)};
})();
