"""Independent arithmetic, geometric consistency, and no-spoiler checks for all 50 items."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json, math, re, subprocess, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
NS='{http://www.w3.org/2000/svg}'

def expected_answers():
    def length(n,unit='cm'):return f'${n}\\text{{ {unit}}}$'
    def area(n,unit='cm'):return f'${n}\\text{{ {unit}}}^{{2}}$'
    # Recompute from the problem statements, without reading drawing parameters.
    square_side_sum=68//4
    square_small=(square_side_sum-3)//2
    width_r9=(64//2)//4
    pairs=[(a,144//a) for a in range(1,13) if 144%a==0 and 2*(a+144//a)==50]
    assert pairs==[(9,16)]
    values={
        'S':[area(8*8),length(4*13,'m'),area((68//4)**2),length(4*math.isqrt(196)),length(6*7),length(4*3*4),area((9+2)**2-9**2),area(15**2-9**2,'m'),length(4*math.isqrt(18*8)),area(square_small**2+(square_small+3)**2)],
        'R':[area(12*7),length(2*(15+4)),length(2*(96//8+8)),area(22*(70//2-22)),length(2*(18//3+12)),f'B, by {area(11*13-9*15)}',length(sum([11,7-3,2,3,11-2,7])),area(16*12-(16-4)*(12-4)),area(width_r9*(3*width_r9)),f'{length(pairs[0][1])} and {length(pairs[0][0])}'],
        'P':[area(11*6),length(2*(15+8)),area(13*7),length(108//18),length(58//2-19),area(12*5-12*5),area(16*9//2),length(9*14//18),area((50//2-11)*7),length(2*(120//8+(120//8-3)))],
        'T':[area(14*8//2),length(9+10+13),length(2*45//15),area(12*7//2),area(16*5//2),length((38-12)//2),area(18*10//2),area(12*(11-7)//2),area(24*10//2-12*5//2),area(120*3//(2+3+5))],
        'Z':[area((10+16)*5//2),length(8+14+5+5),area(max(8,14)*6//2),length(2*88//(8+14)),length(2*90//6-12),area((7+13)*8//2),area((8+20)*8//2),area((12+20)*6//2-12*6),length(2*(12*8)//8-9),area((12+(60-12-13-13))*12//2)]
    }
    return {f'{prefix}{i}':a for prefix,answers in values.items() for i,a in enumerate(answers,1)}

def node_data():
    code="""const fs=require('fs'),g=require('./geometry.js'),b=JSON.parse(fs.readFileSync('content/geometry.json'));
    console.log(JSON.stringify({bank:g.renderBank(b),models:b.problems.map(p=>p.diagramSpec.panels.map(x=>g.geometryFor(x)))}));"""
    return json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT,text=True))

def polygon_area(points):
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1])))/2

def polygon_perimeter(points):
    return sum(math.dist(a,b) for a,b in zip(points,points[1:]+points[:1]))

def numeric_label(s):
    m=re.fullmatch(r'(\d+(?:\.\d+)?) (?:cm|m)',s)
    return float(m[1]) if m else None

def run():
    source=json.loads((ROOT/'content/geometry.json').read_text())
    assert len(source['problems'])==50 and source['defaultCount']==50 and source['difficultyScale']==5
    assert Counter(p['group'] for p in source['problems'])==dict.fromkeys(['square','rectangle','parallelogram','triangle','trapezoid'],10)
    assert len({p['id'] for p in source['problems']})==50
    assert len({p['q'] for p in source['problems']})==50
    expected=expected_answers();rendered=node_data();bank=rendered['bank'];diagrams=bank['diagrams']
    assert len(diagrams)==50
    for p,models in zip(source['problems'],rendered['models']):
        assert p['answer']==expected[p['code']],(p['code'],p['answer'],expected[p['code']])
        assert p['level'] in range(1,6)
        for field in ['q','answer','hint','solution','imageAlt']:
            value=p[field];assert isinstance(value,str) and value.strip(),(p['code'],field)
            assert '\u2014' not in value,(p['code'],'em dash')
            if field!='imageAlt':
                assert value.count('$')%2==0,(p['code'],field,'math delimiters')
                assert value.count('{')==value.count('}'),(p['code'],field,'braces')
                assert not re.search(r'\\frac[^{]',value),(p['code'],'brace fractions for MathML fallback')
        assert not re.search(r'pythag|hypotenuse|sine|cosine|tangent|similarity|\\sqrt',p['solution'],re.I),p['code']
        for panel,model in zip(p['diagramSpec']['panels'],models):
            pts=model['outline'];assert polygon_area(pts)>0
            for key,value in panel.get('labels',{}).items():
                n=numeric_label(value)
                if n is None:continue
                if key in model['edges']:actual=math.dist(*model['edges'][key])
                elif key=='cell':actual=panel.get('cell',panel.get('side'))
                elif key=='inner':actual=model['w']-2*panel['border']
                elif key in ('border','cutWidth','cutHeight'):actual=panel[key]
                else:raise AssertionError((p['code'],'unverified length label',key))
                assert math.isclose(n,actual,rel_tol=1e-8),(p['code'],key,n,actual)
            for key,actual in [('heightLabel',model['h']),('smallHeightLabel',panel.get('topHeight')),('cutLabel',model['w']*panel.get('topHeight',0)/model['h'])]:
                n=numeric_label(panel.get(key,''))
                if n is not None:assert math.isclose(n,actual,rel_tol=1e-8),(p['code'],key,n,actual)
            if panel.get('equalLegs'):
                assert math.isclose(math.dist(*model['edges']['left']),math.dist(*model['edges']['right']),rel_tol=1e-8)
            caption=panel.get('caption','')
            m=re.search(r'(?:Total )?(Area|Perimeter) = (\d+)',caption)
            if m:
                actual=polygon_area(pts) if m[1]=='Area' else polygon_perimeter(pts)
                assert math.isclose(float(m[2]),actual,rel_tol=1e-8),(p['code'],caption,actual)
        svg=diagrams['geometry-'+p['id']];root=ET.fromstring(svg)
        assert root.tag==NS+'svg' and root.attrib['viewBox']=='0 0 640 400'
        assert root.find(NS+'title').text==p['imageAlt']
        allowed={'svg','title','rect','polygon','line','polyline','text'}
        for element in root.iter():
            assert element.tag.removeprefix(NS) in allowed,(p['code'],element.tag)
            assert not any(k.lower().startswith('on') or 'href' in k.lower() for k in element.attrib)
        # Numbers can occur in coordinates, but visible labels and accessibility text
        # may only repeat numerical givens from the question. This catches solved
        # lengths in reverse problems as well as leaked final answers.
        givens=set(re.findall(r'\d+(?:\.\d+)?',p['q']))
        visible=' '.join((node.text or '') for node in root.iter() if node.tag in (NS+'text',NS+'title'))
        leaked=set(re.findall(r'\d+(?:\.\d+)?',visible))-givens
        assert not leaked,(p['code'],'non-given number exposed in diagram',leaked)
    output=ROOT/'test-results';output.mkdir(exist_ok=True)
    (output/'geometry-validation.json').write_text(json.dumps({'passed':True,'questions':50,'diagrams':50,'checks':['independent answers','ten per shape','geometric consistency','given-only labels and alternative text','SVG safety','MathML-compatible notation']},indent=2)+'\n')
    print('Verified all 50 answers, 50 valid SVGs, shape counts, givens and no-spoiler labels.')
if __name__=='__main__':run()
