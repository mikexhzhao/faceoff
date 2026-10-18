"""Geometry UI regression and native-SVG layout checks. Screenshots contain givens only."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from urllib.parse import unquote
import argparse, functools, json, re, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from browser import mount, act, fast, select, THEMES
ROOT=Path(__file__).resolve().parents[1]

def run(embedded=False,executable=None):
    out=ROOT/'test-results';images=out/'geometry';images.mkdir(parents=True,exist_ok=True)
    source=json.loads((ROOT/'content/geometry.json').read_text())
    questions=source['problems'];by_text={p['q']:p for p in questions}
    index=len(json.loads((ROOT/'g57_bank.json').read_text())['sets'])
    handler=functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT))
    server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    checks=[];errors=[];layout=[]
    def ok(name,condition=True):
        assert condition,name
        checks.append(name)
    def current(page):return by_text[page.locator('.question-text').get_attribute('data-source')]
    def image_ready(page):page.wait_for_function('document.querySelector(".geometry-figure img").complete && document.querySelector(".geometry-figure img").naturalWidth>0')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=executable,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='reduce')
        context.route(re.compile(r'^https://'),lambda r:r.abort())
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        mount(page,embedded,base)
        select(page,index)
        ok('Full bank is the default',page.get_by_label('Number of questions').input_value()=='50')
        ok('Five shapes plus mixed option',page.get_by_label('Shapes').locator('option').count()==6)
        fast(page,'start')
        svg_page=context.new_page();svg_page.set_viewport_size({'width':640,'height':400})
        for p in questions:
            ok(p['code']+' order',current(page)['id']==p['id'])
            ok(p['code']+' answers initially absent',page.locator('.answer-box,.solution-box,.hint-box').count()==0)
            ok(p['code']+' solution control initially absent',page.locator('[data-action="solution"]').count()==0)
            ok(p['code']+' explicit difficulty',page.locator(f'[aria-label="Difficulty {p["level"]} of 5"]').count()==1)
            image_ready(page)
            image=page.locator('.geometry-figure img')
            ok(p['code']+' alt contains givens',image.get_attribute('alt')==p['imageAlt'])
            box=image.bounding_box();ok(p['code']+' aspect ratio',abs(box['width']/box['height']-640/400)<.01)
            svg=unquote(image.get_attribute('src').split(',',1)[1])
            svg_page.set_content('<html><body style="margin:0;background:#fffef9">'+svg+'</body></html>')
            boxes=svg_page.locator('text:not([aria-hidden])').evaluate_all('els=>els.map(el=>{const b=el.getBBox();return {text:el.textContent,x:b.x,y:b.y,w:b.width,h:b.height};})')
            for b in boxes:
                ok(p['code']+' label inside SVG: '+b['text'],b['x']>=2 and b['y']>=2 and b['x']+b['w']<=638 and b['y']+b['h']<=398)
            overlaps=[]
            for i,a in enumerate(boxes):
                for b in boxes[i+1:]:
                    dx=min(a['x']+a['w'],b['x']+b['w'])-max(a['x'],b['x'])
                    dy=min(a['y']+a['h'],b['y']+b['h'])-max(a['y'],b['y'])
                    if dx>1 and dy>1:overlaps.append([a['text'],b['text']])
            layout.append({'code':p['code'],'labels':boxes,'overlaps':overlaps})
            ok(p['code']+' labels do not overlap',not overlaps)
            svg_page.screenshot(path=str(images/(p['code']+'.png')))
            if p['code'] in ['S5','S8','R7','R8','P3','T5','T9','T10','Z6','Z8','Z10']:
                page.screenshot(path=str(images/(p['code']+'-app.png')),full_page=True)
            fast(page,'next')
        ok('Fiftieth question finishes the round',page.locator('.result').count()==1)
        svg_page.close()
        # Every shape filter must select its ten original questions, not the first ten in the bank.
        for group in source['groups']:
            select(page,index);page.get_by_label('Shapes').select_option(group['id'])
            ok(group['name']+' count',page.get_by_label('Number of questions').input_value()=='10')
            ok(group['name']+' max',page.get_by_label('Number of questions').get_attribute('max')=='10')
            fast(page,'start');seen=[]
            for _ in range(10):
                q=current(page);seen.append(q['id']);ok(group['name']+' membership',q['group']==group['id']);fast(page,'next')
            ok(group['name']+' unique questions',len(set(seen))==10)
        # A twelve-question mixed shuffle contains every shape, as evenly as possible.
        select(page,index);page.get_by_label('Number of questions').fill('12')
        page.locator('[data-setting="shuffle"]').select_option('true');fast(page,'start')
        mixed=[]
        for _ in range(12):mixed.append(current(page));fast(page,'next')
        counts=Counter(q['group'] for q in mixed)
        ok('Mixed shuffle includes all five shapes',len(counts)==5)
        ok('Mixed shuffle balanced',max(counts.values())-min(counts.values())<=1)
        ok('Mixed shuffle without repeats',len({q['id'] for q in mixed})==12)
        # Short filtered rounds retain their own ordering during review and jumping.
        select(page,index);page.get_by_label('Shapes').select_option('triangle');page.get_by_label('Number of questions').fill('3');fast(page,'start')
        q=current(page);ok('Short triangle round starts correctly',q['code']=='T1')
        fast(page,'hint');ok('Hint is separate',page.locator('.hint-box .math').get_attribute('data-source')==q['hint'])
        fast(page,'answer');fast(page,'solution')
        ok('Answer and solution reveal',page.locator('.answer-box .math').get_attribute('data-source')==q['answer'] and page.locator('.solution-box .math').get_attribute('data-source')==q['solution'])
        fast(page,'answer');ok('Hide answer also hides solution',page.locator('.answer-box,.solution-box').count()==0)
        fast(page,'next');ok('Next clears hints and reveals',page.locator('.hint-box,.answer-box,.solution-box').count()==0)
        fast(page,'next');fast(page,'next');fast(page,'review')
        ok('Review starts at filtered first question',current(page)['code']=='T1')
        ok('Review paused',page.locator('#pause-button').inner_text()=='Resume')
        fast(page,'next');ok('Review keeps filtered order',current(page)['code']=='T2')
        fast(page,'jump');page.locator('input[name="round"]').fill('3');page.locator('[data-form="jump"] button').click()
        ok('Jump uses the filtered round',current(page)['code']=='T3')
        # Zoom is a givens-only dialog, and time spent inspecting a diagram is not charged.
        select(page,index);page.get_by_label('Shapes').select_option('triangle');fast(page,'start')
        fast(page,'jump');page.locator('input[name="round"]').fill('5');page.locator('[data-form="jump"] button').click()
        image_ready(page);fast(page,'zoom-diagram');before=page.locator('#time-value').inner_text();page.wait_for_timeout(1150)
        ok('Zoom pauses the timer',page.locator('#time-value').inner_text()==before)
        ok('Zoom shows only the diagram',page.locator('dialog .answer-box,dialog .solution-box,dialog .hint-box').count()==0)
        ok('Zoom alt is unchanged',page.locator('dialog img').get_attribute('alt')==current(page)['imageAlt'])
        act(page,'close-dialog');ok('Zoom returns focus',page.locator('[data-action="zoom-diagram"]').evaluate('(el)=>el===document.activeElement'))
        for theme in THEMES:
            fast(page,'themes');page.locator(f'[data-theme="{theme}"].theme-tile').click()
            image_ready(page);ok(theme+' keeps question',current(page)['code']=='T5')
            page.screenshot(path=str(images/(theme+'-desktop.png')),full_page=True)
            for width in [390,320]:
                page.set_viewport_size({'width':width,'height':844})
                ok(theme+f' {width}px no page overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                box=page.locator('.geometry-figure img').bounding_box()
                ok(theme+f' {width}px diagram fits',box['x']>=0 and box['x']+box['width']<=width+1)
            page.screenshot(path=str(images/(theme+'-mobile.png')),full_page=True)
            page.set_viewport_size({'width':1440,'height':1100})
        if embedded:
            select(page,index);fast(page,'home')
            page.evaluate("delete window.__files['content/geometry.json'];document.querySelector('#app').insertAdjacentHTML('beforeend','<button data-action=retry id=geometry-retry>Retry</button>')")
            page.locator('#geometry-retry').click();page.wait_for_selector('.error')
            ok('A failed geometry fetch preserves all old sets',page.locator('.set-card').count()==39)
            page.evaluate('(b)=>window.__files["content/geometry.json"]=b',source)
            fast(page,'retry');page.wait_for_function("document.querySelectorAll('.set-card').length===40")
            ok('Geometry fetch can be retried',page.locator('.error').count()==0)
        ok('No JavaScript errors',not errors)
        browser.close()
    server.shutdown()
    (out/'geometry-label-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
    report={'passed':True,'questions':50,'diagrams':50,'checks':len(checks),'themes':THEMES,'errors':errors}
    (out/'geometry-browser-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--embedded',action='store_true');parser.add_argument('--executable');args=parser.parse_args();run(args.embedded,args.executable)
