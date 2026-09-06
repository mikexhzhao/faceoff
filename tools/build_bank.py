"""Build the curated bank and deterministic SVG diagrams. Standard library only."""
from __future__ import annotations
import json
import math
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INK, ACCENT, FILL, PAPER = '#304638', '#ac432b', '#d5e3c6', '#fffef9'

def el(tag, **attrs):
    return '<'+tag+' '+ ' '.join(f'{k.replace("_", "-")}="{html.escape(str(v), quote=True)}"' for k,v in attrs.items())+'/>'

def line(x1,y1,x2,y2,**kw):
    return el('line',x1=round(x1,3),y1=round(y1,3),x2=round(x2,3),y2=round(y2,3),stroke=kw.pop('stroke',INK),stroke_width=kw.pop('stroke_width',3),**kw)

def text(x,y,t,size=22,**kw):
    attrs=dict(x=round(x,3),y=round(y,3),text_anchor=kw.pop('text_anchor','middle'),fill=INK,font_size=size,font_family='Arial, sans-serif',**kw)
    return el('text',**attrs)[:-2]+'>'+html.escape(str(t))+'</text>'

def polygon(points,**kw):
    return el('polygon',points=' '.join(f'{x:.3f},{y:.3f}' for x,y in points),fill=kw.pop('fill',FILL),stroke=kw.pop('stroke',INK),stroke_width=3,stroke_linejoin='round',**kw)

def dot(x,y,r=6,fill=INK):return el('circle',cx=x,cy=y,r=r,fill=fill)

def rect(x,y,w,h,**kw):return el('rect',x=x,y=y,width=w,height=h,fill=kw.pop('fill',FILL),stroke=INK,stroke_width=2.5,**kw)

def tick(a,b):
    x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
    dx,dy=b[0]-a[0],b[1]-a[1]; n=math.hypot(dx,dy)
    return line(x-8*dy/n,y+8*dx/n,x+8*dy/n,y-8*dx/n,stroke=ACCENT)

def arc(cx,cy,r,a,b):
    # Angles are measured anticlockwise in mathematical coordinates.
    f=lambda d:(cx+r*math.cos(math.radians(d)),cy-r*math.sin(math.radians(d)))
    x,y=f(a);u,v=f(b)
    return el('path',d=f'M{x:.3f},{y:.3f} A{r},{r} 0 {int(b-a>180)} 0 {u:.3f},{v:.3f}',fill='none',stroke=ACCENT,stroke_width=2)

def svg(title,body,w=520,h=320):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img"><title>{html.escape(title)}</title>'+el('rect',width=w,height=h,rx=12,fill=PAPER)+body+'</svg>'

def regular(n,cx=260,cy=165,r=110,angle=-90):
    return [(cx+r*math.cos(math.radians(angle+360*i/n)),cy+r*math.sin(math.radians(angle+360*i/n))) for i in range(n)]

def diagrams():
    d={}
    d['fraction-strip']=svg('Three eighths of an equal-part strip', ''.join(rect(60+50*i,45,50,70,fill=FILL if i<3 else PAPER) for i in range(8)),h=160)
    a=''
    for i in range(4):a+=line(140+80*i,75,140+80*i,155,stroke=ACCENT,stroke_width=6,stroke_linecap='round')
    for j in range(3):
        a+=line(140+80*j,75,220+80*j,75,stroke=ACCENT,stroke_width=6,stroke_linecap='round')
        a+=line(140+80*j,155,220+80*j,155,stroke=ACCENT,stroke_width=6,stroke_linecap='round')
    d['matchsticks']=svg('Three adjacent matchstick squares',a,h=225)
    ox,oy=260,235
    d['straight-angle']=svg('Adjacent angles on a straight line',line(65,oy,455,oy)+line(ox,oy,ox+160*math.cos(math.radians(62)),oy-160*math.sin(math.radians(62)))+arc(ox,oy,54,0,62)+arc(ox,oy,70,62,180)+text(211,172,'118°')+text(320,211,'x'))
    ta,tb=math.tan(math.radians(48)),math.tan(math.radians(67));dx=260*tb/(ta+tb)
    A,B,C=(110,270),(370,270),(110+dx,270-dx*ta)
    d['triangle-angles']=svg('Triangle with base angles 48 and 67 degrees',polygon([A,B,C])+arc(*A,38,0,48)+arc(*B,38,113,180)+text(155,249,'48°',20)+text(331,246,'67°',20)+text(C[0]-4,C[1]+49,'x')+text(92,292,'A',20)+text(390,292,'B',20)+text(C[0],C[1]-18,'C',20))
    A,B,C=(180,270),(340,270),(260,270-80/math.tan(math.radians(20)))
    d['isosceles']=svg('Isosceles triangle with a 40-degree vertex angle',polygon([A,B,C])+tick(A,C)+tick(B,C)+arc(*C,48,250,290)+text(260,126,'40°',20)+text(210,251,'x')+text(310,251,'x'))
    A,B,C=(110,260),(350,260),(230,260-120*math.sqrt(3))
    d['equilateral-exterior']=svg('Exterior angle of an equilateral triangle',polygon([A,B,C])+line(*B,460,260)+tick(A,B)+tick(A,C)+tick(B,C)+arc(*B,52,0,120)+text(386,202,'x'))
    pts=regular(5)
    d['pentagon']=svg('Pentagon partitioned into three triangles',polygon(pts)+line(*pts[0],*pts[2],stroke=ACCENT,stroke_width=2)+line(*pts[0],*pts[3],stroke=ACCENT,stroke_width=2))
    d['rectangle']=svg('Eight-centimetre by five-centimetre rectangle',rect(100,55,320,200)+text(260,35,'8 cm')+text(460,165,'5 cm'))
    d['triangle-area']=svg('Triangle with base twelve and perpendicular height five',polygon([(60,250),(420,250),(285,100)])+line(285,100,285,250,stroke=ACCENT,stroke_dasharray='7 5')+el('path',d='M285 235 H300 V250',fill='none',stroke=ACCENT,stroke_width=2)+text(240,288,'12 cm')+text(246,192,'5 cm'))
    d['parallelogram']=svg('Parallelogram with perpendicular height',polygon([(85,250),(355,250),(435,130),(165,130)])+line(165,130,165,250,stroke=ACCENT,stroke_dasharray='7 5')+el('path',d='M165 235 H180 V250',fill='none',stroke=ACCENT,stroke_width=2)+text(220,288,'9 cm')+text(204,199,'4 cm'))
    # Front face, right face and top face. The three hidden edges meet at the back lower-left corner.
    A,B,C,D=(155,267),(295,267),(295,71),(155,71)
    Ap,Bp,Cp,Dp=(245,221),(385,221),(385,25),(245,25)
    body=polygon([A,B,C,D])+polygon([B,Bp,Cp,C],fill='#e9ddc6')+polygon([D,C,Cp,Dp],fill='#efcfba')
    body+=line(*A,*Ap,stroke_dasharray='6 5')+line(*Ap,*Bp,stroke_dasharray='6 5')+line(*Ap,*Dp,stroke_dasharray='6 5')
    body+=text(225,303,'4 cm')+text(364,268,'3 cm')+text(116,176,'7 cm')
    d['prism']=svg('Rectangular prism with dimensions four, three and seven centimetres',body)
    body=polygon([(130,65),(274,65),(274,137),(370,137),(370,257),(130,257)])
    body+=line(274,65,370,65,stroke='#9b9b8b',stroke_dasharray='6 5',stroke_width=2)+line(370,65,370,137,stroke='#9b9b8b',stroke_dasharray='6 5',stroke_width=2)
    body+=text(250,292,'10 cm')+text(86,169,'8 cm')+text(322,45,'4 cm')+text(413,110,'3 cm')
    d['l-shape']=svg('L-shape formed by removing a four-by-three corner from a ten-by-eight rectangle',body)
    body=rect(106,48,308,220,fill='#edd2b7')+rect(128,70,264,176)+text(260,160,'12 m × 8 m',24)+line(403,158,455,204,stroke=ACCENT,stroke_width=2)+dot(403,158,3,ACCENT)+text(455,232,'1 m')
    d['garden']=svg('One-metre border outside a twelve-by-eight-metre garden',body)
    def grid(xmax,ymax,step=40,ox=70,oy=270):
        body=''
        for x in range(xmax+1):
            X=ox+x*step; body+=line(X,oy,X,oy-ymax*step,stroke='#d0d9c6',stroke_width=1)+text(X,oy+23,str(x),15)
        for y in range(1,ymax+1):
            Y=oy-y*step;body+=line(ox,Y,ox+xmax*step,Y,stroke='#d0d9c6',stroke_width=1)+text(ox-21,Y+5,str(y),15)
        body+=line(ox,oy,ox+xmax*step+25,oy,stroke_width=2)+line(ox,oy,ox,oy-ymax*step-15,stroke_width=2)
        body+=text(ox+xmax*step+38,oy+7,'x',18)+text(ox-16,oy-ymax*step-8,'y',18)
        return body
    d['coordinate-a']=svg('First-quadrant coordinate grid with point A at two, three',grid(8,6)+dot(150,150,6,ACCENT)+text(169,137,'A',20),h=315)
    body=grid(8,5,45,70,267)
    pts=[(115,222),(385,222),(385,87),(115,87)]
    body+=polygon(pts,fill='none',stroke=ACCENT)
    for p,n,t in zip(pts,'ABCD',[(95,247),(405,247),(405,78),(95,78)]):body+=dot(*p,5,ACCENT)+text(*t,n,18)
    d['coordinate-rectangle']=svg('Coordinate rectangle with three known corners and corner D',body)
    d['hexagon']=svg('Regular hexagon',polygon(regular(6,r=108,angle=0)))
    body='';cx,cy,r=260,160,108
    for i in range(8):
        a,b=math.radians(-90+45*i),math.radians(-45+45*i)
        x,y=cx+r*math.cos(a),cy+r*math.sin(a);u,v=cx+r*math.cos(b),cy+r*math.sin(b)
        body+=el('path',d=f'M{cx},{cy} L{x:.3f},{y:.3f} A{r},{r} 0 0 1 {u:.3f},{v:.3f} Z',fill=FILL if i<3 else PAPER,stroke=INK,stroke_width=2.5)
    body+=dot(cx,cy,7)+line(cx,cy,cx,cy-67,stroke=ACCENT,stroke_width=4)+polygon([(cx-7,cy-66),(cx+7,cy-66),(cx,cy-81)],fill=ACCENT,stroke=ACCENT)
    d['spinner']=svg('Eight equal sectors, three shaded',body)
    body=el('circle',cx=260,cy=170,r=104,stroke='#b5c4a9',stroke_width=2,fill='none')
    for i,(x,y) in enumerate(regular(8,260,170,104)):
        body+=dot(round(x,3),round(y,3),18,FILL)+text(x,y+7,i,20)
    d['clock-stones']=svg('Eight stones numbered zero through seven clockwise',body)
    body=''
    for x,weight,bit in zip([52,160,268,376],[8,4,2,1],[1,0,1,1]):
        body+=text(x+46,75,weight,22)+rect(x,100,92,100,fill=FILL if bit else PAPER,rx=8)+text(x+46,165,bit,42)
    d['binary-cards']=svg('Four binary places with weights eight, four, two, one and digits one, zero, one, one',body,h=260)
    corners={'A':(160,75),'B':(360,75),'C':(360,245),'D':(160,245)}
    def network(edges):
        body=''.join(line(*corners[a],*corners[b]) for a,b in edges)
        for n,(x,y) in corners.items():body+=dot(x,y,7)+text(x+(-18 if n in 'AD' else 18),y+(-20 if n in 'AB' else 32),n)
        return body
    d['square-diagonal']=svg('Square network with diagonal A C',network(['AB','BC','CD','DA','AC']))
    d['complete-four']=svg('Four vertices with all six edges; diagonal crossing is not a vertex',network(['AB','BC','CD','DA','AC','BD']))
    pts={'A':(80,160),'B':(245,65),'C':(245,255),'D':(440,160)}
    body=''.join(line(*pts[a],*pts[b]) for a,b in ['AB','AC','BC','BD','CD'])
    for x,y,t in [(150,93,2),(151,240,5),(273,168,1),(352,93,6),(354,240,2)]:body+=text(x,y,t,22)
    for n,(x,y) in pts.items():body+=dot(x,y,7)
    for n,(x,y) in {'A':(48,168),'B':(245,36),'C':(245,294),'D':(472,168)}.items():body+=text(x,y,n)
    d['weighted-network']=svg('Weighted network with AB two, AC five, BC one, BD six and CD two',body)
    body=''
    for i in range(4):body+=line(132+85*i,60,132+85*i,230)
    for j in range(3):body+=line(132,60+85*j,387,60+85*j)
    d['rectangle-grid']=svg('Two rows and three columns of square cells',body)
    dots=''.join(dot(132+85*i,60+85*j,3) for i in range(4) for j in range(3))
    d['grid-path']=svg('Grid three edges wide and two edges high, from bottom-left A to top-right B',body+dots+dot(132,230,7,ACCENT)+dot(387,60,7,ACCENT)+text(109,260,'A')+text(411,46,'B'))
    body=''
    for row in range(4):
        for col in range(4):
            x,y=156+52*col,40+52*row
            body+=rect(x,y,52,52,fill='#74915b' if (row+col)%2==0 else '#f2ead2')
            if (row,col) in [(0,0),(3,3)]:body+=rect(x+2,y+2,48,48,fill=PAPER)+line(x+10,y+10,x+42,y+42,stroke=ACCENT,stroke_width=4)+line(x+42,y+10,x+10,y+42,stroke=ACCENT,stroke_width=4)
    d['checkerboard-four']=svg('Four-by-four checkerboard with opposite same-colour corner squares removed',body,h=290)
    return d

def build():
    sets=[]; current=None
    for number,raw in enumerate((ROOT/'content/sets.txt').read_text(encoding='utf-8').splitlines(),1):
        t=raw.strip()
        if not t:continue
        if t.startswith('@'):
            slug,name,strand,kind,grade,symbol=t[1:].split('|')
            current=dict(id=slug,name=name,strand=strand,kind=kind,grade=grade,symbol=symbol,lesson=[],problems=[])
            sets.append(current)
        elif t.startswith('!'):
            assert current is not None,f'Lesson before header: {number}'
            current['lesson'].append(t[1:])
        else:
            assert current is not None,f'Problem before header: {number}'
            fields=[v.strip() for v in t.split(' || ')]
            assert len(fields) in (4,6),f'Bad field count on line {number}'
            q,a,h,s=fields[:4];i=len(current['problems'])+1
            p=dict(id=f'{current["id"]}-{i:02}',q=q,answer=a,hint=h,solution=s,level=min(3,1+(i-1)//4))
            if len(fields)==6:p.update(diagram=fields[4],imageAlt=fields[5])
            current['problems'].append(p)
    assert len(sets)==16
    assert all(len(s['problems'])==12 for s in sets)
    diagrams_ = diagrams()
    for s in sets:
        for p in s['problems']:
            assert not p.get('diagram') or p['diagram'] in diagrams_,p['id']
    out=ROOT/'sets/g57';out.mkdir(parents=True,exist_ok=True)
    assets=ROOT/'assets/diagrams';assets.mkdir(parents=True,exist_ok=True)
    for k,v in diagrams_.items():(assets/(k+'.svg')).write_text(v,encoding='utf-8')
    for s in sets:
        standalone={**s,'problems':[{**p,**({'image':'../../assets/diagrams/'+p['diagram']+'.svg'} if p.get('diagram') else {})} for p in s['problems']]}
        (out/(s['id']+'.json')).write_text(json.dumps(standalone,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    bank=dict(version=1,sets=sets,diagrams=diagrams_)
    (ROOT/'g57_bank.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'question_bank.json').write_text(json.dumps({'sets':[s['id']+'.json' for s in sets]},indent=2)+'\n',encoding='utf-8')
    print(f'Built {len(sets)} sets, {sum(len(s["problems"]) for s in sets)} questions, {len(diagrams_)} diagrams.')
    return bank

if __name__=='__main__':build()
