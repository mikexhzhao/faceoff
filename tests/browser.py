"""Browser regression tests. Install playwright; run with --embedded in a network-restricted renderer."""
from __future__ import annotations
import argparse, functools, json, re, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
THEMES=['studio','notebook','arcade','sweet','orbit','volcano','stadium','paper']

def mount(page, embedded, base):
    if not embedded:
        page.goto(base,wait_until='domcontentloaded')
    else:
        source=ROOT.joinpath('index.html').read_text()
        source=re.sub(r'<script.*?</script>','',source)
        source=re.sub(r'<link[^>]+>','',source)
        source=source.replace('<head>','<head><base href="https://faceoff.test/">')
        page.set_content(source)
        page.add_style_tag(content=ROOT.joinpath('faceoff-next.css').read_text())
        files={str(p.relative_to(ROOT)):json.loads(p.read_text()) for p in ROOT.rglob('*.json')}
        page.evaluate('''files=>{window.__files=files;window.fetch=async url=>{const path=decodeURIComponent(new URL(url,document.baseURI).pathname.slice(1));return new Response(JSON.stringify(files[path]||{}),{status:files[path]?200:404});}}''',files)
        page.add_script_tag(content=ROOT.joinpath('faceoff-next.js').read_text())
    page.wait_for_selector('.set-card')
    page.wait_for_function("document.querySelectorAll('.set-card').length===39")

def act(page, action):page.locator(f'[data-action="{action}"]').first.click()
def fast(page,action):page.evaluate('(a)=>document.querySelector(`[data-action="${a}"]`).click()',action)
def select(page,index):
    if page.locator('[data-action="confirm-home"]').is_visible():act(page,'confirm-home')
    if page.locator('body').get_attribute('data-view')!='library':
        act(page,'home')
        if page.locator('[data-action="confirm-home"]').is_visible():act(page,'confirm-home')
    page.locator(f'[data-action="select-set"][data-index="{index}"]').click()

def run(embedded=False, executable=None):
    out=ROOT/'test-results';out.mkdir(exist_ok=True)
    handler=functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT))
    server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    checks=[];errors=[]
    def ok(name,condition=True):
        assert condition,name
        checks.append(name)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=executable,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        # Verify mathematical and UI fallbacks independently of external CDNs.
        context.route(re.compile(r'^https://'),lambda route:route.abort())
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        mount(page,embedded,base)
        ok('39 sets including all 23 originals',page.locator('.set-card').count()==39)
        ok('No partial-bank warning',page.locator('.error').count()==0)
        page.screenshot(path=str(out/'studio-library.png'),full_page=True)
        page.locator('[data-filter="Grade 5–7"]').click();ok('Nine core sets',page.locator('.set-card').count()==9)
        page.locator('[data-filter="Enrichment"]').click();ok('Seven enrichment sets',page.locator('.set-card').count()==7)
        page.locator('[data-filter="Originals"]').click();ok('23 originals',page.locator('.set-card').count()==23)
        page.locator('[data-filter="All"]').click()
        select(page,5)
        ok('No question preview in setup',page.locator('.question-text').count()==0)
        page.get_by_label('Player or team name').fill('Maple');page.locator('[data-form="player"] button').click()
        page.get_by_label('Player or team name').fill('Cedar');page.locator('[data-form="player"] button').click()
        page.locator('[data-setting="duration"]').select_option('30')
        act(page,'start')
        ok('First round',page.locator('.round-label').inner_text()=='1 / 12')
        page.locator('[data-action="score"][data-delta="1"]').first.click()
        ok('Add point',page.locator('.score-value').first.inner_text()=='1')
        page.locator('[data-action="score"][data-delta="-1"]').first.click()
        ok('Zero score is preserved',page.locator('.score-value').first.inner_text()=='0')
        act(page,'undo');ok('Undo score',page.locator('.score-value').first.inner_text()=='1')
        act(page,'reset-timer');page.wait_for_timeout(1150)
        ok('Timer runs',int(page.locator('#time-value').inner_text())<30)
        act(page,'pause');before=page.locator('#time-value').inner_text();page.wait_for_timeout(1150)
        ok('Pause freezes timer',page.locator('#time-value').inner_text()==before)
        act(page,'pause');act(page,'answer');before=page.locator('#time-value').inner_text();page.wait_for_timeout(1150)
        ok('Answer freezes timer',page.locator('#time-value').inner_text()==before)
        act(page,'solution');ok('Solution appears',page.locator('.solution-box').count()==1)
        act(page,'answer');ok('Hiding answer also hides solution',page.locator('.solution-box').count()==0)
        act(page,'hint');ok('Hint works',page.locator('.hint-box').count()==1)
        act(page,'hint')
        for theme in THEMES:
            act(page,'themes')
            ok('Nine selectable modes',page.locator('.theme-tile').count()==9)
            page.locator(f'.theme-tile[data-theme="{theme}"]').click()
            ok('Theme '+theme,page.locator('body').get_attribute('data-theme')==theme)
            ok('Theme preserves question and scores',page.locator('.round-label').inner_text()=='1 / 12' and page.locator('.score-value').first.inner_text()=='1')
            page.screenshot(path=str(out/f'{theme}-game.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            ok(theme+' mobile has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            page.screenshot(path=str(out/f'{theme}-mobile.png'),full_page=True)
            page.set_viewport_size({'width':1440,'height':1000})
        print('Theme checks complete',flush=True)
        act(page,'themes');page.locator('[data-setting="motion"]').select_option('off');act(page,'close-dialog')
        ok('Motion can be disabled',page.locator('body').get_attribute('data-motion')=='off')
        act(page,'settings');page.locator('[data-setting="font"]').fill('52');act(page,'close-dialog')
        ok('Text size updates',page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--question-size").trim()')=='52px')
        act(page,'settings');page.locator('[data-setting="font"]').fill('32');act(page,'close-dialog')
        act(page,'players');page.get_by_label('Player or team name').fill('<img src=x onerror=alert(1)>');page.locator('[data-form="player"] button').click();act(page,'close-dialog')
        ok('Names are escaped',page.locator('.scores img').count()==0)
        act(page,'jump');page.locator('input[name="round"]').fill('12');page.locator('[data-form="jump"] button').click()
        ok('Go to question',page.locator('.round-label').inner_text()=='12 / 12')
        act(page,'next');ok('Round finishes',page.locator('.result').count()==1)
        act(page,'review');before=page.locator('#time-value').inner_text();page.wait_for_timeout(1150)
        ok('Review paused',page.locator('#time-value').inner_text()==before)
        act(page,'next');ok('Review remains paused on navigation',page.locator('#pause-button').inner_text()=='Resume')
        act(page,'home');act(page,'confirm-home')
        # Exercise every new question, answer, hint, solution and diagram.
        bank=json.loads((ROOT/'g57_bank.json').read_text());seen=0;seen_images=0
        for i,s in enumerate(bank['sets']):
            print('Checking set',s['id'],flush=True)
            select(page,i)
            if s['kind']=='Enrichment':ok('Enrichment defaults to untimed '+s['id'],page.locator('[data-setting="duration"]').input_value()=='0')
            fast(page,'lesson');ok('Three lesson paragraphs',page.locator('.lesson-paragraph').count()==3);fast(page,'close-dialog')
            fast(page,'start')
            for q in s['problems']:
                ok(q['id']+' prompt',page.locator('.question-text').get_attribute('data-source')==q['q'])
                fast(page,'hint');fast(page,'answer');fast(page,'solution')
                ok(q['id']+' answer and solution',page.locator('.answer-box .math').get_attribute('data-source')==q['answer'] and page.locator('.solution-box .math').get_attribute('data-source')==q['solution'])
                ok(q['id']+' math fallback',page.locator('.math').evaluate_all('(els)=>els.every(e=>!e.textContent.includes("$"))'))
                if 'diagram' in q:
                    page.wait_for_function('document.querySelector(".diagram").complete && document.querySelector(".diagram").naturalWidth>0');seen_images+=1
                seen+=1;fast(page,'next')
            fast(page,'home')
        ok('All new questions traversed',seen==192)
        ok('Diagrams loaded',seen_images>=25)
        # Failed fetch is visible and recoverable rather than dropping sets silently.
        if embedded:
            page.evaluate("delete window.__files['g57_bank.json']")
            page.evaluate("document.querySelector('#app').insertAdjacentHTML('beforeend','<button data-action=retry id=test-retry>Retry</button>')")
            page.locator('#test-retry').click();page.wait_for_selector('.error')
            ok('Partial load warning displayed',page.locator('.set-card').count()==23)
            page.evaluate('(bank)=>window.__files["g57_bank.json"]=bank',bank)
            act(page,'retry');page.wait_for_function("document.querySelectorAll('.set-card').length===39")
            ok('Retry restores missing bank',page.locator('.error').count()==0)
        if not embedded:
            context.route(re.compile(r'/classic\.html$'),lambda r:r.fulfill(status=200,content_type='text/html',body='<html><body></body></html>'))
        # Classic navigation. The source hash test separately proves preservation.
        act(page,'themes');page.locator('.theme-tile[data-theme="classic"]').click()
        ok('Classic frame selected',page.locator('#classic-shell').is_visible() and page.locator('#classic-frame').get_attribute('src')=='./classic.html')
        page.locator('#classic-themes').click();page.locator('.theme-tile[data-theme="studio"]').click()
        ok('Return from Classic',page.locator('#app').is_visible() and page.locator('#classic-frame').get_attribute('src')=='about:blank')
        ok('No JavaScript errors',not errors)
        if not embedded:
            page.reload();page.wait_for_selector('.set-card')
            ok('Saved theme persists',page.locator('body').get_attribute('data-theme')=='studio')
            select(page,0);ok('Saved players persist',page.locator('.player-edit').count()==3)
            # Separately check CDN typesetting, with no interception, and original Classic React.
            online=browser.new_context(viewport={'width':1440,'height':1000})
            live=online.new_page();mount(live,False,base)
            live.wait_for_function('typeof window.renderMathInElement === "function"',timeout=45000)
            select(live,0);act(live,'start');act(live,'answer')
            ok('KaTeX CDN renders formulas',live.locator('.katex').count()>0)
            tex=[]
            for group in bank['sets']:
                texts=group['lesson']+[p[k] for p in group['problems'] for k in ['q','answer','hint','solution']]
                for text in texts:tex.extend(re.findall(r'\$([^$]+)\$',text))
            failures=live.evaluate("xs=>xs.flatMap(t=>{try{katex.renderToString(t,{throwOnError:true});return [];}catch(e){return [t+': '+e.message];}})",tex)
            ok('Every LaTeX expression compiles',not failures)
            live.screenshot(path=str(out/'katex-game.png'),full_page=True)
            live.goto(base+'classic.html',wait_until='domcontentloaded')
            live.wait_for_selector('#root button',timeout=45000)
            ok('Classic React app starts',live.locator('#root').inner_text().find('Leaderboard')>=0)
            live.wait_for_function("document.querySelectorAll('#root select option').length===23",timeout=45000)
            ok('Classic loads its complete original bank',live.locator('#root select option').count()==23)
            live.screenshot(path=str(out/'classic.png'),full_page=True)
            online.close()
        motion_context=browser.new_context(viewport={'width':1000,'height':850},reduced_motion='no-preference')
        motion_context.route(re.compile(r'^https://'),lambda r:r.abort())
        motion_page=motion_context.new_page();mount(motion_page,embedded,base)
        select(motion_page,0)
        motion_page.get_by_label('Player or team name').fill('Team')
        motion_page.locator('[data-form="player"] button').click();act(motion_page,'start')
        for theme in ['arcade','sweet','orbit','volcano','paper']:
            act(motion_page,'themes');motion_page.locator(f'.theme-tile[data-theme="{theme}"]').click()
            motion_page.locator('[data-action="score"][data-delta="1"]').first.click()
            motion_page.wait_for_timeout(100)
            ok(theme+' effects draw',motion_page.evaluate("Array.from(document.querySelector('#effects').getContext('2d').getImageData(0,0,1000,850).data).some((v,i)=>i%4===3&&v>0)"))
        motion_context.close()
        report={'mode':'embedded' if embedded else 'http','checks':len(checks),'questions':seen,'diagram_occurrences':seen_images,'themes':THEMES+['classic'],'errors':errors,'passed':True}
        (out/'browser-report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
        browser.close()
    server.shutdown()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--embedded',action='store_true');p.add_argument('--executable');args=p.parse_args();run(args.embedded,args.executable)
