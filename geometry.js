/* Deterministic SVG geometry. Only explicit labels and givens enter the image text. */
(function (root) {
'use strict';
const INK='#304638', HEIGHT='#a9432f', PAPER='#fffef9', FILL='#e2ecdd', SHADE='#edc28a';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const positive=(n,name)=>{if(!Number.isFinite(n)||n<=0)throw Error('Invalid '+name);return n;};
const finite=(n,name)=>{if(!Number.isFinite(n))throw Error('Invalid '+name);return n;};
const point=(x,y)=>[x,y];
const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
const near=(a,b)=>Math.abs(a-b)<1e-7;
const mid=(a,b)=>[(a[0]+b[0])/2,(a[1]+b[1])/2];
const rotate=(p,angle)=>{const a=angle*Math.PI/180;return [p[0]*Math.cos(a)-p[1]*Math.sin(a),p[0]*Math.sin(a)+p[1]*Math.cos(a)];};
function geometryFor(p) {
  if(!p||typeof p!=='object')throw Error('Missing geometry panel');
  const kind=p.kind;let w,h,outline;
  if(['square','rectangle','frame','squareGrid','joinedSquares','notchedRectangle'].includes(kind)){
    w=kind==='square'?p.side:kind==='squareGrid'?p.cell*p.rows:kind==='joinedSquares'?2*p.side:p.width;
    h=kind==='square'?p.side:kind==='squareGrid'?w:kind==='joinedSquares'?p.side:p.height;
    positive(w,'width');positive(h,'height');
    outline=[[0,0],[w,0],[w,h],[0,h]];
    if(kind==='notchedRectangle'){
      positive(p.cutWidth,'cut width');positive(p.cutHeight,'cut height');
      if(p.cutWidth>=w||p.cutHeight>=h)throw Error('Corner cut consumes rectangle');
      outline=[[0,0],[w,0],[w,h-p.cutHeight],[w-p.cutWidth,h-p.cutHeight],[w-p.cutWidth,h],[0,h]];
    }
  }else if(kind==='parallelogram'||kind==='trapezoid'){
    w=positive(p.base,'base');h=positive(p.height,'height');
    const top=kind==='parallelogram'?w:positive(p.top,'top base');
    let offset=p.offset;
    if(offset===undefined){
      if(kind==='parallelogram'&&p.side!==undefined){
        positive(p.side,'side');if(p.side<h)throw Error('Side shorter than height');
        // Drawing construction only. Student solutions do not use this calculation.
        offset=Math.sqrt(p.side*p.side-h*h);
      }else offset=kind==='trapezoid'?(w-top)/2:w*.22;
    }
    finite(offset,'offset');outline=[[0,0],[w,0],[offset+top,h],[offset,h]];
  }else if(kind==='triangle'){
    w=positive(p.base,'base');let x=p.apex;
    h=p.height;
    if(p.left!==undefined&&p.right!==undefined){
      positive(p.left,'left side');positive(p.right,'right side');
      if(p.left+p.right<=w||Math.abs(p.left-p.right)>=w)throw Error('Impossible triangle');
      // Construct a valid drawing from the supplied side lengths, never a student step.
      x=(p.left*p.left+w*w-p.right*p.right)/(2*w);
      h=Math.sqrt(p.left*p.left-x*x);
    }
    positive(h,'height');finite(x,'apex');outline=[[0,0],[w,0],[x,h]];
  }else throw Error('Unknown geometry kind: '+kind);
  const A=outline[0],B=outline[1],C=outline[2],D=outline.at(-1);
  const edges={bottom:[A,B],left:[A,D],right:[B,C]};
  if(kind!=='triangle')edges.top=[D,C];
  const angle=finite(p.angle??0,'angle');
  return {outline,edges,w,h,angle};
}
function sceneFor(p){
  const g=geometryFor(p),{outline:pts,edges,w,h}=g;
  const A=pts[0],B=pts[1],C=pts[2],D=pts.at(-1),labels=p.labels||{};
  const scene={...g,polygons:[],lines:[],dimensions:[],texts:[],rights:[],ticks:[],parallels:[],caption:p.caption||''};
  const poly=(points,fill=FILL,stroke=true)=>scene.polygons.push({points,fill,stroke});
  const line=(a,b,dashed=false,colour=INK)=>scene.lines.push({a,b,dashed,colour});
  const dimension=(a,b,text,options={})=>{if(text!==undefined&&text!==null&&text!=='')scene.dimensions.push({a,b,text,...options});};
  const right=(v,a,b)=>scene.rights.push({v,a,b});
  poly(pts,p.shade||p.kind==='frame'?PAPER:FILL);
  if(p.kind==='notchedRectangle'){
    const corner=[w,h],cutTop=[w-p.cutWidth,h],cutRight=[w,h-p.cutHeight];
    line(cutTop,corner,true);line(corner,cutRight,true);
    dimension(cutTop,corner,labels.cutWidth);
    dimension(cutRight,corner,labels.cutHeight);
  }
  if(p.kind==='frame'){
    const t=positive(p.border,'border');if(t*2>=Math.min(w,h))throw Error('Frame has no opening');
    scene.polygons=[];poly(pts,SHADE);
    const inner=[[t,t],[w-t,t],[w-t,h-t],[t,h-t]];poly(inner,PAPER);
    dimension([t,h/2],[w-t,h/2],labels.inner,{normal:[0,-1],measure:true,offset:25});
    dimension([w*.54,h-t],[w*.54,h],labels.border,{normal:[1,0],measure:true,offset:35});
  }
  if(p.kind==='joinedSquares'){
    line([p.side,0],[p.side,h],true);
    dimension([0,h],[p.side,h],labels.cell);
  }
  if(p.kind==='squareGrid'){
    if(!Number.isInteger(p.rows)||p.rows<2||p.rows>8)throw Error('Invalid square grid');
    for(let i=1;i<p.rows;i++){line([i*p.cell,0],[i*p.cell,h]);line([0,i*p.cell],[w,i*p.cell]);}
    dimension([0,h],[p.cell,h],labels.cell);
  }
  if(p.strips){
    if(!Number.isInteger(p.strips)||p.strips<2||p.strips>8)throw Error('Invalid strips');
    if(p.shade==='firstStrip')poly([[0,0],[w/p.strips,0],[w/p.strips,h],[0,h]],SHADE,false);
    for(let i=1;i<p.strips;i++)line([w*i/p.strips,0],[w*i/p.strips,h]);
  }
  if(p.diagonal){
    if(pts.length!==4)throw Error('Diagonal needs a quadrilateral');
    if(p.shade==='firstTriangle')poly([A,B,C],SHADE,false);
    line(A,C);
  }
  if(p.kind==='triangle'&&p.topHeight!==undefined){
    const topHeight=positive(p.topHeight,'top height');if(topHeight>=h)throw Error('Invalid triangle cut');
    const y=h-topHeight,t=y/h,E=[C[0]*t,y],F=[w+(C[0]-w)*t,y];
    if(p.shade==='lower')poly([A,B,F,E],SHADE,false);
    line(E,F);dimension(E,F,p.cutLabel,{normal:[0,-1],offset:22});
    const foot=[C[0],y];line(C,foot,true,HEIGHT);right(foot,C,F);
    dimension(C,foot,p.smallHeightLabel,{normal:[1,0],offset:p.smallHeightOffset??34});
  }
  if(p.kind==='triangle'&&p.ratios){
    if(!Array.isArray(p.ratios)||p.ratios.length!==3||p.ratios.some(n=>!Number.isFinite(n)||n<=0))throw Error('Invalid base ratio');
    const sum=p.ratios.reduce((a,b)=>a+b,0),x1=w*p.ratios[0]/sum,x2=w*(p.ratios[0]+p.ratios[1])/sum;
    if(p.shade==='middleTriangle')poly([[x1,0],[x2,0],C],SHADE,false);
    line(C,[x1,0]);line(C,[x2,0]);
    const xs=[0,x1,x2,w];p.ratios.forEach((r,i)=>dimension([xs[i],0],[xs[i+1],0],r+' parts',{offset:32}));
  }
  if(p.kind==='trapezoid'&&p.corners){
    const leftFoot=[D[0],0],rightFoot=[C[0],0];
    if(D[0]<0||C[0]>w)throw Error('Corner split requires both feet on base');
    if(p.shade==='corners'){poly([A,leftFoot,D],SHADE,false);poly([B,C,rightFoot],SHADE,false);}
    line(C,rightFoot,true,HEIGHT);right(rightFoot,C,B);
    if(!p.heightLabel){line(D,leftFoot,true,HEIGHT);right(leftFoot,D,B);}
  }
  if(p.heightLabel){
    let top=p.kind==='triangle'?C:(p.altitudeFrom==='right'?C:D),foot=[top[0],0];
    if(p.heightExternal){
      const x=p.heightExternal==='left'?Math.min(...pts.map(v=>v[0]))-w*.12:Math.max(...pts.map(v=>v[0]))+w*.12;
      line(top,[x,h],true,HEIGHT);top=[x,h];foot=[x,0];
    }
    if(foot[0]<0)line(foot,A,true,HEIGHT);
    if(foot[0]>w)line(B,foot,true,HEIGHT);
    line(top,foot,true,HEIGHT);
    right(foot,top,[foot[0]+(foot[0]>=w?-1:1),0]);
    dimension(top,foot,p.heightLabel,{normal:[p.heightSide==='left'?-1:1,0],offset:p.heightOffset??34});
  }
  if(p.rightAngle)right(A,B,C);
  if(p.equalLegs){
    if(!near(dist(...edges.left),dist(...edges.right)))throw Error('Unequal sides given equal ticks');
    scene.ticks.push(edges.left,edges.right);
  }
  if(p.kind==='trapezoid')scene.parallels.push(edges.bottom,edges.top);
  Object.keys(edges).forEach(name=>dimension(...edges[name],labels[name]));
  // Restore the outer boundary over shaded pieces, without adding any measurements.
  scene.lines.push(...pts.map((v,i)=>({a:v,b:pts[(i+1)%pts.length],dashed:false,colour:INK})));
  const all=[...pts,...scene.lines.flatMap(l=>[l.a,l.b]),...scene.polygons.flatMap(q=>q.points)];
  const rotated=all.map(v=>rotate(v,g.angle));
  scene.bounds={minX:Math.min(...rotated.map(v=>v[0])),maxX:Math.max(...rotated.map(v=>v[0])),minY:Math.min(...rotated.map(v=>v[1])),maxY:Math.max(...rotated.map(v=>v[1]))};
  return scene;
}
function renderDiagram(spec,alt){
  if(!spec||!Array.isArray(spec.panels)||!spec.panels.length||spec.panels.length>2)throw Error('Expected one or two diagram panels');
  const scenes=spec.panels.map(sceneFor),W=640,H=400,panelWidth=W/scenes.length;
  const leftPad=scenes.length===1?90:58,rightPad=scenes.length===1?90:58,top=90,bottom=320;
  const scales=scenes.map(s=>Math.min((panelWidth-leftPad-rightPad)/(s.bounds.maxX-s.bounds.minX),(bottom-top)/(s.bounds.maxY-s.bounds.minY)));
  const scale=Math.min(...scales);
  const n=x=>{if(!Number.isFinite(x))throw Error('Non-finite drawing coordinate');return Number(x.toFixed(3));};
  let body='';
  const text=(x,y,t,size=27)=>{
    const attrs=`x="${n(x)}" y="${n(y)}" text-anchor="middle" dominant-baseline="central" font-family="Arial, sans-serif" font-size="${size}" font-weight="500"`;
    // Two passes also preserve legibility in SVG-to-image/PDF exporters.
    return `<text ${attrs} aria-hidden="true" fill="none" stroke="${PAPER}" stroke-width="5" stroke-linejoin="round">${esc(t)}</text><text ${attrs} fill="${INK}">${esc(t)}</text>`;
  };
  scenes.forEach((s,i)=>{
    const b=s.bounds,cx=(b.minX+b.maxX)/2,cy=(b.minY+b.maxY)/2;
    const map=v=>{const q=rotate(v,s.angle);return [panelWidth*(i+.5)+(q[0]-cx)*scale,(top+bottom)/2-(q[1]-cy)*scale];};
    const vector=v=>{const q=rotate(v,s.angle);return [q[0],-q[1]];};
    const path=points=>points.map(v=>map(v).map(n).join(',')).join(' ');
    const line=(a,b,colour=INK,dashed=false,width=2.7)=>`<line x1="${n(a[0])}" y1="${n(a[1])}" x2="${n(b[0])}" y2="${n(b[1])}" stroke="${colour}" stroke-width="${width}"${dashed?' stroke-dasharray="7 5"':''}/>`;
    for(const q of s.polygons)body+=`<polygon points="${path(q.points)}" fill="${q.fill}" stroke="${q.stroke?INK:'none'}" stroke-width="2.7" stroke-linejoin="round"/>`;
    for(const l of s.lines)body+=line(map(l.a),map(l.b),l.colour,l.dashed,l.colour===HEIGHT?2.2:2.7);
    for(const r of s.rights){
      const v=map(r.v),a=map(r.a),b=map(r.b),la=dist(v,a),lb=dist(v,b);
      if(la<.01||lb<.01)throw Error('Degenerate right-angle marker');
      const ua=[(a[0]-v[0])/la,(a[1]-v[1])/la],ub=[(b[0]-v[0])/lb,(b[1]-v[1])/lb];
      if(Math.abs(ua[0]*ub[0]+ua[1]*ub[1])>1e-6)throw Error('Marker is not a right angle');
      const z=Math.min(12,la*.22,scale*1.2);
      const P=[v[0]+z*ua[0],v[1]+z*ua[1]],Q=[P[0]+z*ub[0],P[1]+z*ub[1]],R=[v[0]+z*ub[0],v[1]+z*ub[1]];
      body+=`<polyline points="${[P,Q,R].map(p=>p.map(n).join(',')).join(' ')}" fill="none" stroke="${HEIGHT}" stroke-width="2"/>`;
    }
    for(const edge of s.ticks){
      const a=map(edge[0]),b=map(edge[1]),m=mid(a,b),d=dist(a,b),dx=-(b[1]-a[1])/d*7,dy=(b[0]-a[0])/d*7;
      body+=line([m[0]-dx,m[1]-dy],[m[0]+dx,m[1]+dy],INK,false,2.8);
    }
    for(const edge of s.parallels){
      const a=map(edge[0]),b=map(edge[1]),m=mid(a,b),d=dist(a,b),u=[(b[0]-a[0])/d,(b[1]-a[1])/d],v=[-u[1],u[0]];
      const pts=[[-7,-5],[1,0],[-7,5]].map(([x,y])=>[m[0]+x*u[0]+y*v[0],m[1]+x*u[1]+y*v[1]]);
      body+=`<polyline points="${pts.map(p=>p.map(n).join(',')).join(' ')}" fill="none" stroke="${INK}" stroke-width="2.2"/>`;
    }
    const centre=map([s.outline.reduce((a,v)=>a+v[0],0)/s.outline.length,s.outline.reduce((a,v)=>a+v[1],0)/s.outline.length]);
    for(const d of s.dimensions){
      const a=map(d.a),b=map(d.b),m=mid(a,b),length=dist(a,b);if(length<.01)throw Error('Zero-length dimension');
      let normal;
      if(d.normal)normal=vector(d.normal);
      else {normal=[-(b[1]-a[1])/length,(b[0]-a[0])/length];if(normal[0]*(m[0]-centre[0])+normal[1]*(m[1]-centre[1])<0)normal=normal.map(x=>-x);}
      const unit=Math.hypot(...normal);normal=normal.map(x=>x/unit);
      if(d.measure){body+=line(a,b,HEIGHT,false,1.8);for(const v of [a,b])body+=line([v[0]-5*normal[0],v[1]-5*normal[1]],[v[0]+5*normal[0],v[1]+5*normal[1]],HEIGHT,false,1.8);}
      const offset=d.offset??(Math.abs(normal[0])>.98?(scenes.length===1?44:38):34);
      body+=text(m[0]+normal[0]*offset,m[1]+normal[1]*offset,d.text,scenes.length===1?27:25);
    }
    if(s.caption)body+=text(panelWidth*(i+.5),22,s.caption,scenes.length===1?26:24);
  });
  body+=`<text x="320" y="386" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#65736b">Diagram not to scale</text>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" role="img"><title>${esc(alt)}</title><rect width="${W}" height="${H}" rx="12" fill="${PAPER}"/>${body}</svg>`;
}
function renderBank(source){
  if(!source||!Array.isArray(source.problems)||source.id!=='area-perimeter-50')throw Error('Invalid geometry bank');
  const diagrams={},ids=new Set();
  const problems=source.problems.map(p=>{
    if(!p||typeof p.id!=='string'||ids.has(p.id)||typeof p.imageAlt!=='string'||!p.imageAlt.trim())throw Error('Invalid geometry problem');
    ids.add(p.id);
    const diagram='geometry-'+p.id;
    diagrams[diagram]=renderDiagram(p.diagramSpec,p.imageAlt);
    const {diagramSpec,...problem}=p;
    return {...problem,diagram,geometryDiagram:true};
  });
  return {sets:[{...source,problems}],diagrams};
}
const api={geometryFor,sceneFor,renderDiagram,renderBank};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
else root.FaceoffGeometry=api;
})(globalThis);
