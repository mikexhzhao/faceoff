"""Independent answer checks for every new problem.
Uses exact fractions, enumeration, shortest paths and backwards game solving.
Run from any directory with Python 3.10 or later.
"""
from __future__ import annotations
import json, math, re
from fractions import Fraction as F
from itertools import combinations, product, permutations
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def T(x): return '$'+str(x)+'$'
def U(x,u):return T(str(x)+r'\text{ '+u+'}')
def A(x):return T(str(x)+r'^\circ')
def Q(n,d=1):
    f=F(n,d)
    return T(str(f.numerator)) if f.denominator==1 else T(r'\frac{'+str(f.numerator)+'}{'+str(f.denominator)+'}')
def area(n,unit,power):return T(str(n)+r'\text{ '+unit+'}^{'+str(power)+'}')
def pair(x,y):return T(f'({x},{y})')
def factors(n):return [d for d in range(1,n+1) if n%d==0]
def prime(n):return n>1 and len(factors(n))==2

def canonical(x):return re.sub(r'\s+','',str(x)).replace('$','')

def grid_paths(w,h):
    ways=[[1]*(w+1) for _ in range(h+1)]
    for y in range(1,h+1):
        for x in range(1,w+1):ways[y][x]=ways[y-1][x]+ways[y][x-1]
    return ways[h][w]

@lru_cache(None)
def winning(n,moves,last_loses=False):
    # With no counters, the player to move wins only under the last-counter-loses rule.
    if n==0:return last_loses
    return any(not winning(n-m,moves,last_loses) for m in moves if m<=n)

def good_moves(n,moves,last_loses=False):return [m for m in moves if m<=n and not winning(n-m,moves,last_loses)]

@lru_cache(None)
def two_piles(a,b):
    return any(not two_piles(a-i,b) for i in range(1,a+1)) or any(not two_piles(a,b-i) for i in range(1,b+1))

def reachable_differences(values):
    if len(values)==1:return set(values)
    out=set()
    for i,j in combinations(range(len(values)),2):
        rest=[v for k,v in enumerate(values) if k not in (i,j)]
        out |= reachable_differences(tuple(rest+[abs(values[i]-values[j])]))
    return out

def domino_tilable(cells):
    if not cells:return True
    x,y=min(cells)
    return any((x+dx,y+dy) in cells and domino_tilable(cells-{(x,y),(x+dx,y+dy)}) for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)])

def shortest(edges,start,end):
    best={start:0};todo=[start]
    while todo:
        u=todo.pop()
        for a,b,w in edges:
            v=b if a==u else a if b==u else None
            if v is not None and best.get(v,math.inf)>best[u]+w:best[v]=best[u]+w;todo.append(v)
    return best[end]

def guarantees(n,k):return (n-1)*k+1

def expected():
    e={}
    e['fractions']=[Q(3,8),Q(6,9),Q(max(F(5,8),F(7,12))),T(28*3//4),Q(F(2,3)+F(5,6)),Q(F(7,8)-F(1,3)),T(F(9,4)/F(3,8)),T(18/F(3,5)),Q(1-F(1,3)-F(1,4)),Q((1-F(2,3))/2),T(r'\frac{7}{14}'),U(18/(F(3,4)-F(3,10)),'L')]
    e['ratios']=[Q(F('0.375')),T('0.678'),U('0.08','m'),T(80//4),T(str(100*18//24)+r'\%'),T(40*3//8),U('4.5','km'),T(18/F('0.4')),U(100*F(6,5)*F(4,5),'dollars'),U(1800*2//9,'mL'),T(str((10+5)*100//30)+r'\%'),U(float(F(6)/(F(3,4)+F(3,6))),'km/h')]
    e['factors']=[T(','.join(map(str,[n for n in range(11,20) if prime(n)]))),T(','.join(map(str,factors(24)))),T(math.lcm(6,8)),T(math.gcd(36,48)),T(next(d for d in range(10) if (402+10*d)%9==0)),T(r'2^{3}\times3^{2}'),T(len(factors(36))),'9:24',T(next(n for n in range(51,200) if n%6==n%9==0)),T(r'0\text{ or }6'),T(sum((n%2==0) != (n%5==0) for n in range(1,101))),U(min(2*(d+60//d) for d in factors(60)),'cm')]
    e['algebra']=[T(13+3),T(5*7-2),T('x='+str(42-17)),T('x='+str((25-4)//3)),T(len(set([('h',x,y) for x in range(10) for y in (0,1)]+[('v',x,0) for x in range(11)]))),T((17+3)//2),T(6*7),T(next(n+1 for n in range(1,51) if n+n+1==51)),U((25-4)//3,'km'),T(12-(19-12)),T((53-5)//4+1),T(next(n for n in range(10,100) if n==3*sum(map(int,str(n)))))]
    e['angles']=[A(180-118),A(180-48-67),A(180-90-34),A((180-40)//2),A(360-90-85-110),A(180-60),A(360-90-125),A(360//4),A(3*180),A(4*180//6),A(180*3//6),A((180-(180-112))//2)]
    e['measurement']=[area(8*5,'cm',2),U(2*(8+5),'cm'),area(12*5//2,'cm',2),area(9*4,'cm',2),area(4*3*7,'cm',3),U(240,'cm'),area(10*8-4*3,'cm',2),U(sum([10,8-3,4,3,10-4,8]),'cm'),T(6**3//3**3),U(float(F('7.2')*250/1000),'km'),U(1800//(30*20),'cm'),area(14*10-12*8,'m',2)]
    e['coordinates']=[pair(2+4,3+2),U(5-(-2),'units'),pair(-3,-2),pair(-4,-5),pair(2,(1+9)//2),pair(1,4),U((7-1)*(4-1),'square units'),pair(-1,3),pair(-(1+3),2-1),T(6),pair(-(7-3),2),pair(4*(2-1),4)]
    e['data']=[T(sorted([2,5,7,9,12])[2]),T(sum([3,7,8])//3),T(25-12),Q(sum(n>4 for n in range(1,7)),6),Q(4,4+3+5),Q(3,8),T(4*10-sum([6,9,11])),T(5*8-sum([4,6,8,10])),Q(sum(sum(bits)==1 for bits in product([0,1],repeat=2)),4),Q(sum(a+b==7 for a,b in product(range(1,7),repeat=2)),36),Q(sum(a<3 and b<3 for a,b in permutations(range(5),2)),20),'Median: 6 minutes']
    e['money']=[U('8.25','dollars'),U('7.15','dollars'),U(80*F(85,100),'dollars'),U('49.50','dollars'),'Pack B',U(18*F(2,3)*5,'dollars'),T(int((18-3)/F('1.5'))),U(120-48-27-35,'dollars'),U('101.70','dollars'),T(str((120-96)*100//120)+r'\%'),'15 dollars off; 3 dollars more',T(math.ceil((150-80)/(12-5)))]
    e['clock']=['3 o\'clock',T(17%5),'Friday','Green',T(7**2%10),T(3**7%10),T(next(n for n in range(21,100) if n%5==2)),T(sum(n%4==1 for n in range(1,31))),'06:00',T(next(n for n in range(1,100) if n%3==2 and n%5==3)),T(2026%9),T(next(n for n in range(1,9) if (3*n)%8==0))]
    e['binary']=[T(int('1011',2)),format(13,'04b'),format(int('111',2)+1,'b'),T(max(int(''.join(bits),2) for bits in product('01',repeat=4))),T(len(list(product([0,1],repeat=5)))),T(int('10110',2)),''.join(chr(65+(ord(c)-65+3)%26) for c in 'MATH'),''.join(chr(65+(ord(c)-65-2)%26) for c in 'ECV'),T('10110'.count('1')%2),T(2**7-1),T(next(n for n in range(10) if 2**n>=20)),T(sum(sum(b)==3 for b in product([0,1],repeat=6)))]
    edges=['AB','BC','CD','DA','AC'];degrees={v:sum(v in edge for edge in edges) for v in 'ABCD'}
    e['networks']=[T(degrees['A']),T(sum(degrees.values())),T(len(list(combinations('ABCD',2)))),T(5-1),T(18//2),'A or C','No',T(shortest([('A','B',2),('A','C',5),('B','C',1),('B','D',6),('C','D',2)],'A','D')),T(len(list(combinations('ABCDE',2)))),T(sum([1,2,2,3])//2),T(2),'No']
    e['counting']=[T(3*2),T(len(list(product('01',repeat=3)))),T(len(list(permutations('ABCD')))),T(len(list(combinations(range(5),2)))),T(grid_paths(3,2)),T(len(list(permutations('123',2)))),T(sum(p[0]!='0' for p in permutations('0123'))),T(len(list(combinations(range(6),2)))),T(len(list(permutations(range(5),3)))),T(len(list(product(combinations(range(3),2),combinations(range(4),2))))),T(grid_paths(4,3)),T(sum('7' in str(n) for n in range(1,101)))]
    board={(x,y) for x in range(4) for y in range(4)}-{(0,0),(3,3)}
    assert not domino_tilable(board)
    assert 0 in reachable_differences((3,7,10))
    reachable={0};todo=[0]
    while todo:
        mask=todo.pop()
        for a,b in combinations(range(8),2):
            nxt=mask^(1<<a)^(1<<b)
            if nxt not in reachable:reachable.add(nxt);todo.append(nxt)
    assert not any(mask.bit_count()==1 for mask in reachable)
    e['parity']=['Odd','Even','No','No','No',T(sum(range(1,11))),'No','Dark','Yes: replace 10 and 7 by 3, then 3 and 3 by 0.','No','No',T(sum(range(1,10))-8)]
    # Enumerate extremal choices for the nontrivial guarantees.
    no_pair_max=max(sum(counts) for counts in product(range(6),repeat=3) if sum(n//2 for n in counts)<2)
    independent_max=max(len(c) for r in range(10) for c in combinations(range(1,10),r) if all(b-a!=1 for a,b in combinations(c,2)))
    avoid_sum11=max(len(c) for r in range(11) for c in combinations(range(1,11),r) if all(a+b!=11 for a,b in combinations(c,2)))
    e['pigeonhole']=[T(4+1),T(12+1),T(math.ceil(10/3)),T(2*5+1),T(math.ceil(31/6)),T(5+1),T(avoid_sum11+1),T(8+1),'Yes',T(independent_max),T(no_pair_max+1),T(16+1)]
    assert good_moves(4,(1,2))==[1] and good_moves(8,(1,2))==[2]
    assert not winning(12,(1,2,3)) and not winning(20,(1,2,3))
    assert not winning(7,(1,2),True) and not winning(10,(1,3))
    nim_moves=[('a',i) for i in range(1,4) if not two_piles(3-i,5)]+[('b',i) for i in range(1,6) if not two_piles(3,5-i)]
    assert nim_moves==[('b',2)]
    e['games']=[T(good_moves(4,(1,2))[0]),T(good_moves(8,(1,2))[0]),T(good_moves(10,(1,2,3))[0]),'No',T(good_moves(21,(1,2,3,4))[0]),'The second player',T(good_moves(21,(1,2,3))[0]),'No',T(good_moves(8,(1,2),True)[0]),'The second player',T(8-1),'Remove 2 from the pile of 5.']
    return e

def run():
    bank=json.loads((ROOT/'g57_bank.json').read_text())
    checks=expected();fail=[];n=0
    for s in bank['sets']:
        assert len(checks[s['id']])==len(s['problems'])
        for p,expected_answer in zip(s['problems'],checks[s['id']]):
            n+=1
            if canonical(p['answer'])!=canonical(expected_answer):fail.append(f'{p["id"]}: {p["answer"]!r} != {expected_answer!r}')
    assert not fail,'\n'.join(fail)
    print(f'{n} answers independently checked; enumeration and strategy checks passed.')
if __name__=='__main__':run()
