{
const D=window.__DATA__;
const S=D.shiurim.map((s,i)=>({...s,id:i,r:s.r||"רבני הישיבה"}));
const PAL=["#1a2f7a","#0f6e64","#a8322b","#6b3fa6","#8a5d00","#2b6fa3","#9b2f63","#3d6b21"];
const order=[...new Set(S.map(s=>s.y))];
const Y={};D.yeshivot.forEach(y=>{const i=order.indexOf(y.id);Y[y.id]={...y,c:i<0?"#7b8397":PAL[i%PAL.length]}});
const CH=D.channels;
const T=["גמרא","הלכה","תנ\"ך","פרשת השבוע","אמונה ומחשבה","מוסר","חסידות וקבלה","מועדים"];
const REG_ORDER=["צפון","שרון","גוש דן","השפלה","חבל יבנה","ירושלים","בנימין","שומרון","בקעת הירדן","גוש עציון","יהודה","הר חברון","דרום"];
const REG=[...REG_ORDER.filter(g=>D.yeshivot.some(y=>y.reg===g)),...new Set(D.yeshivot.map(y=>y.reg).filter(g=>!REG_ORDER.includes(g)))];
const L=[["s","עד 15 דקות",d=>d<=15],["m","15 עד 45 דקות",d=>d>15&&d<=45],["l","יותר מ-45 דקות",d=>d>45]];
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const hesder=y=>"https://hesder.org.il/institute/"+encodeURIComponent(y.h);
const ytUrl=r=>r.startsWith("UC")?`https://www.youtube.com/channel/${r}`:`https://www.youtube.com/${r}`;
const short=n=>n.replace(/\s*–.*$/,"");
const st={q:"",topic:"",ys:[],rg:[],r:"",len:[],ao:false,sort:"new"};
try{Object.assign(st,JSON.parse(localStorage.getItem("osh-f2")||"{}"))}catch(e){}
const save=()=>{try{localStorage.setItem("osh-f2",JSON.stringify(st))}catch(e){}};
const heb=dt=>{try{return new Intl.DateTimeFormat("he-u-ca-hebrew",{day:"numeric",month:"long"}).format(new Date(dt))}catch(e){return dt}};
const when=x=>x.yr?x.yr:heb(x.dt);
const norm=s=>s.replace(/["'״׳]/g,"").toLowerCase();
const byNew=(a,b)=>b.dt.localeCompare(a.dt);
const SORTS={new:byNew,short:(a,b)=>(a.d||999)-(b.d||999),long:(a,b)=>(b.d||0)-(a.d||0),az:(a,b)=>a.t.localeCompare(b.t,"he")};
const match=(x,skip)=>{
 if(st.q){const q=norm(st.q).split(/\s+/).filter(Boolean);const h=norm(x.t+" "+x.r+" "+x.c+" "+Y[x.y].n);if(!q.every(w=>h.includes(w)))return false}
 if(skip!=="topic"&&st.topic&&x.c!==st.topic)return false;
 if(skip!=="rg"&&st.rg.length&&!st.rg.includes(Y[x.y].reg))return false;
 if(skip!=="y"&&st.ys.length&&!st.ys.includes(x.y))return false;
 if(skip!=="r"&&st.r&&x.r!==st.r)return false;
 if(skip!=="len"&&st.len.length&&!L.some(l=>st.len.includes(l[0])&&x.d&&l[2](x.d)))return false;
 if(skip!=="ao"&&st.ao&&!x.a)return false;
 return true};
const cnt=(skip,f)=>S.filter(x=>match(x,skip)&&f(x)).length;
const box=(name,val,label,n,on,dot)=>`<label class="opt"><input type="checkbox" name="${name}" value="${esc(val)}" ${on?"checked":""}>${dot?`<span class="dot" style="background:${dot}"></span>`:""}<span>${esc(label)}</span><span class="n">${n}</span></label>`;
const withData=Object.keys(Y).filter(k=>S.some(s=>s.y===k));
const PLAY='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l13 8-13 8z" fill="currentColor"/></svg>';
const PAUSE='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h4v16H6zM14 4h4v16h-4z" fill="currentColor"/></svg>';
const QADD='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h12M3 12h12M3 18h7M18 13v8M14 17h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
const QON='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h12M3 12h12M3 18h7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M14 17l3 3 5-6" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg>';
const VID='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="5" width="14" height="14" rx="3" fill="none" stroke="currentColor" stroke-width="2"/><path d="M16 10l6-3v10l-6-3z" fill="currentColor"/></svg>';

/* ---------- filters ---------- */
function renderFilters(){
 $("chips").innerHTML=[["","הכל"],...T.map(t=>[t,t])].map(([v,l],i)=>`<button type="button" class="chip" data-t="${esc(v)}" aria-pressed="${st.topic===v}"><span class="pn" aria-hidden="true">${i||"0"}</span>${l}</button>`).join("");
 $("fg").innerHTML=REG.filter(g=>withData.some(k=>Y[k].reg===g)).map(g=>box("rg",g,g,cnt("rg",x=>Y[x.y].reg===g),st.rg.includes(g))).join("");
 $("fy").innerHTML=withData.map(k=>box("y",k,short(Y[k].n),cnt("y",x=>x.y===k),st.ys.includes(k),Y[k].c)).join("");
 const rs=[...new Set(S.filter(x=>match(x,"r")).map(x=>x.r))].sort((a,b)=>a.localeCompare(b,"he"));
 if(st.r&&!rs.includes(st.r))rs.unshift(st.r);
 $("fr").innerHTML=`<option value="">כל הרבנים</option>`+rs.map(r=>`<option ${r===st.r?"selected":""}>${esc(r)}</option>`).join("");
 $("fl").innerHTML=L.map(l=>box("len",l[0],l[1],cnt("len",x=>x.d&&l[2](x.d)),st.len.includes(l[0]))).join("");
 $("fa").innerHTML=`<label class="opt"><input type="checkbox" name="ao" ${st.ao?"checked":""}><span>רק שיעורים עם קובץ שמע</span><span class="n">${cnt("ao",x=>x.a)}</span></label><p class="hint">מתנגנים גם כשהמסך כבוי, מתאים לנסיעה.</p>`;
 $("sort").value=st.sort;}

/* ---------- player ----------
   A shiur with an audio file (x.a) plays through <audio>, also in the background.
   A shiur that exists only on YouTube plays in a small, visible YouTube player docked
   above the bar (YouTube's terms don't allow taking the sound alone), driven by the
   same buttons, queue, speed and car controls. No fake clock: if nothing can play,
   the listener is told and the queue moves on. */
const aud=$("aud");
const P={q:[],cur:null,playing:false,rate:1,mode:null,pos:{}};
try{Object.assign(P.pos,JSON.parse(localStorage.getItem("osh-pos")||"{}"));const k=JSON.parse(localStorage.getItem("osh-q")||"null");if(k){P.q=(k.q||[]).filter(i=>S[i]);P.rate=k.rate||1}}catch(e){}
const RATES=[1,1.25,1.5,1.75,2,0.75];
const fmt=t=>{t=Math.max(0,Math.floor(t||0));const h=Math.floor(t/3600),m=Math.floor(t%3600/60),s2=String(t%60).padStart(2,"0");return h?`${h}:${String(m).padStart(2,"0")}:${s2}`:`${m}:${s2}`};
const K=x=>x.v||x.a;
const curX=()=>P.cur==null?null:S[P.cur];
let YTP=null,ytReady=null,ytTimer=null,ytT0=0;
const ytOk=()=>YTP&&typeof YTP.getCurrentTime==="function";
const durOf=x=>{if(!x)return 0;if(x.id===P.cur){if(P.mode==="a"&&isFinite(aud.duration)&&aud.duration>0)return aud.duration;if(P.mode==="yt"&&ytOk()){const d=YTP.getDuration();if(d>0)return d}}return (x.d||45)*60};
const resumeLabel=x=>{const t=P.pos[K(x)];return t&&t>30&&t<durOf(x)-30?`<span class="res nw">ממשיכים מ-${fmt(t)}</span>`:""};
const persist=()=>{try{localStorage.setItem("osh-pos",JSON.stringify(P.pos));localStorage.setItem("osh-q",JSON.stringify({q:P.q,rate:P.rate}))}catch(e){}};
const now=()=>P.mode==="yt"?(ytOk()?YTP.getCurrentTime():ytT0):aud.currentTime;
function setT(t){const x=curX();if(!x)return;t=Math.max(0,Math.min(durOf(x)-1,t));if(P.mode==="yt"){if(ytOk())YTP.seekTo(t,true)}else aud.currentTime=t;P.pos[K(x)]=t;tick()}
let toastT;function toast(m){const el=$("toast");el.textContent=m;el.hidden=false;clearTimeout(toastT);toastT=setTimeout(()=>el.hidden=true,5000)}
function loadYT(){if(ytReady)return ytReady;ytReady=new Promise(res=>{window.onYouTubeIframeAPIReady=()=>res(true);const sc=document.createElement("script");sc.src="https://www.youtube.com/iframe_api";sc.onerror=()=>{ytReady=null;res(false)};document.head.appendChild(sc)});return ytReady}
function showDock(x){$("yDockT").textContent=x.t;$("yDock").hidden=false;document.body.classList.add("hasdock")}
function hideDock(){$("yDock").hidden=true;document.body.classList.remove("hasdock");try{ytOk()&&YTP.stopVideo()}catch(e){}clearInterval(ytTimer)}
function stopAll(){aud.pause();try{ytOk()&&YTP.pauseVideo()}catch(e){}clearInterval(ytTimer)}
function play(id,{fromQueue}={}){
 const x=S[id];if(!x)return;
 if(P.cur===id){toggle();return}
 if(!fromQueue&&!P.q.includes(id))P.q.unshift(id);
 stopAll();P.cur=id;P.playing=true;const t0=P.pos[K(x)]||0;
 if(x.a)playAudio(x,t0);else playYT(x,t0);
 meta();ui();persist();
 $("pbar").classList.add("on");document.body.style.paddingBottom="100px";}
function playAudio(x,t0){P.mode="a";hideDock();aud.src=x.a;aud.playbackRate=P.rate;
 if(t0)aud.addEventListener("loadedmetadata",()=>{try{aud.currentTime=t0}catch(e){}},{once:true});
 aud.play().catch(e=>{if(P.cur!==x.id||P.mode!=="a")return;if(e&&e.name==="NotAllowedError"){P.playing=false;ui()}})}
aud.addEventListener("error",()=>{const x=curX();if(!x||P.mode!=="a"||!aud.getAttribute("src"))return;
 if(x.v){toast("קובץ השמע לא נטען, עוברים לנגן של YouTube.");playYT(x,P.pos[K(x)]||0)}
 else{P.playing=false;ui();toast("קובץ השמע של השיעור הזה לא זמין כרגע. ממשיכים לשיעור הבא.");setTimeout(()=>{if(curX()===x)step(1)},2500)}});
async function playYT(x,t0){P.mode="yt";ytT0=t0;aud.pause();aud.removeAttribute("src");showDock(x);
 const id=x.id,ok=await loadYT();if(P.cur!==id||P.mode!=="yt")return;
 if(!ok||!window.YT||!YT.Player){P.playing=false;ui();toast("הנגן של YouTube לא נטען. בדקו את החיבור לאינטרנט.");return}
 if(!YTP){YTP=new YT.Player("yFrame",{host:"https://www.youtube-nocookie.com",width:"100%",height:"100%",videoId:x.v,
   playerVars:{start:Math.floor(t0),playsinline:1,rel:0,autoplay:1},
   events:{onReady:e=>{try{e.target.setPlaybackRate(P.rate)}catch(_){}if(P.playing&&P.mode==="yt")e.target.playVideo()},onStateChange:ytState,onError:ytErr}})}
 else{YTP.loadVideoById({videoId:x.v,startSeconds:Math.floor(t0)});try{YTP.setPlaybackRate(P.rate)}catch(e){}}
 clearInterval(ytTimer);ytTimer=setInterval(()=>{const c=curX();if(c&&P.mode==="yt"&&ytOk()){const t=YTP.getCurrentTime();if(t>0)P.pos[K(c)]=t;tick()}},1000);
 setTimeout(()=>{if(P.cur===id&&P.mode==="yt"&&P.playing&&ytOk()&&![1,3].includes(YTP.getPlayerState())){P.playing=false;ui();toast("הדפדפן חסם הפעלה אוטומטית. הקישו על ▶ בחלון הווידאו.")}},4000)}
function ytState(e){if(P.mode!=="yt")return;const s=e.data;if(s===0){ended();return}
 if(s===1&&!P.playing){P.playing=true;ui()}else if(s===2&&P.playing){P.playing=false;ui()}}
function ytErr(){const x=curX();toast("הסרטון הזה לא זמין לצפייה באתר. ממשיכים לשיעור הבא.");setTimeout(()=>{if(curX()===x)step(1)},2500)}
function toggle(){if(P.cur==null){if(P.q.length)play(P.q[0],{fromQueue:true});return}
 P.playing=!P.playing;
 if(P.mode==="yt"){if(ytOk())P.playing?YTP.playVideo():YTP.pauseVideo()}else{P.playing?aud.play().catch(()=>{}):aud.pause()}
 ui();persist()}
function step(d){if(P.cur==null)return;let i=P.q.indexOf(P.cur);if(i<0){P.q.unshift(P.cur);i=0}
 if(d<0&&now()>10){setT(0);return}
 const n=P.q[i+d];if(n==null){if(d>0){P.playing=false;stopAll();ui()}return}
 P.cur=null;play(n,{fromQueue:true})}
function ended(){const x=curX();if(x)delete P.pos[K(x)];step(1)}
aud.addEventListener("ended",ended);
aud.addEventListener("timeupdate",()=>{const x=curX();if(x&&P.mode==="a")P.pos[K(x)]=aud.currentTime;tick()});
function meta(){const x=curX();if(!x||!("mediaSession" in navigator))return;
 try{navigator.mediaSession.metadata=new MediaMetadata({title:x.t,artist:x.r,album:"ישיבת "+short(Y[x.y].n)});
  const ms=navigator.mediaSession,h=(a,f)=>{try{ms.setActionHandler(a,f)}catch(e){}};
  h("play",()=>{if(!P.playing)toggle()});h("pause",()=>{if(P.playing)toggle()});
  h("seekbackward",()=>setT(now()-15));h("seekforward",()=>setT(now()+30));
  h("previoustrack",()=>step(-1));h("nexttrack",()=>step(1));
  h("seekto",e=>setT(e.seekTime));
 }catch(e){}}
let lastSave=0;
function tick(){const x=curX();if(!x)return;const t=now(),d=durOf(x),pct=d?t/d*100:0;
 $("pCur").textContent=fmt(t);$("pDur").textContent=fmt(d);$("pSeek").value=Math.round(pct*10);
 $("dCur").textContent=fmt(t);$("dLeft").textContent="-"+fmt(d-t);$("dBar").style.width=pct+"%";
 try{navigator.mediaSession&&navigator.mediaSession.setPositionState&&navigator.mediaSession.setPositionState({duration:d,position:Math.min(t,d),playbackRate:P.rate})}catch(e){}
 if(Date.now()-lastSave>5000){lastSave=Date.now();persist()}}
function ui(){const x=curX();
 const ico=P.playing?PAUSE:PLAY,lbl=P.playing?"השהיה":"הפעלה";
 $("pPlay").innerHTML=ico;$("pPlay").setAttribute("aria-label",lbl);
 $("dPlay").innerHTML=ico+`<span>${lbl}</span>`;$("dPlay").setAttribute("aria-label",lbl);
 $("pSpeed").textContent=P.rate+"×";$("dSpeed").textContent=`מהירות ${P.rate}×`;
 $("qN").textContent=P.q.length;
 if(x){$("pT").textContent=x.t;$("pS").textContent=`${x.r}, ישיבת ${short(Y[x.y].n)}${P.mode==="yt"?", בווידאו":""}`;
  $("dT").textContent=x.t;$("dS").textContent=`${x.r}, ${short(Y[x.y].n)}`;}
 try{navigator.mediaSession&&(navigator.mediaSession.playbackState=P.playing?"playing":"paused")}catch(e){}
 tick();renderQueue();
 document.querySelectorAll("#list .shiur").forEach(li=>{const id=+li.dataset.id,on=id===P.cur,b=li.querySelector(".pbig");
  li.classList.toggle("on",on);b.setAttribute("aria-pressed",on);b.innerHTML=on&&P.playing?PAUSE:PLAY;
  b.setAttribute("aria-label",`${on&&P.playing?"השהיה":"האזנה"}: ${S[id].t}`)});
 document.querySelectorAll("#list [data-q]").forEach(b=>{const on=P.q.includes(+b.dataset.q);b.setAttribute("aria-pressed",on);b.innerHTML=on?QON:QADD;b.setAttribute("aria-label",on?"הסרה מהתור":"הוספה לתור")});
 renderOnair();}
function renderQueue(){$("qList").innerHTML=P.q.length?P.q.map(id=>{const x=S[id];return `<li class="${id===P.cur?"cur":""}"><div><b>${esc(x.t)}</b><div class="count">${esc(x.r)}${x.d?`, ${x.d} דק'`:""}</div></div><button class="ghost" data-qp="${id}" aria-label="השמעה">${id===P.cur&&P.playing?PAUSE:PLAY}</button><button class="ghost" data-qr="${id}" aria-label="הסרה מהתור">✕</button></li>`}).join(""):`<li><div>התור ריק. הוסיפו שיעור לתור, או לחצו "השמעת הכל".</div></li>`}
$("yClose").addEventListener("click",()=>{P.playing=false;hideDock();ui()});
$("pPlay").addEventListener("click",toggle);$("dPlay").addEventListener("click",toggle);
$("pBack").addEventListener("click",()=>setT(now()-15));$("dBack").addEventListener("click",()=>setT(now()-15));
$("pFwd").addEventListener("click",()=>setT(now()+30));$("dFwd").addEventListener("click",()=>setT(now()+30));
$("pPrev").addEventListener("click",()=>step(-1));$("dPrev").addEventListener("click",()=>step(-1));
$("pNext").addEventListener("click",()=>step(1));$("dNext").addEventListener("click",()=>step(1));$("dQueueNext").addEventListener("click",()=>step(1));
const speed=()=>{P.rate=RATES[(RATES.indexOf(P.rate)+1)%RATES.length];aud.playbackRate=P.rate;try{P.mode==="yt"&&ytOk()&&YTP.setPlaybackRate(P.rate)}catch(e){}ui();persist()};
$("pSpeed").addEventListener("click",speed);$("dSpeed").addEventListener("click",speed);
$("pSeek").addEventListener("input",e=>{const x=curX();if(x)setT(e.target.value/1000*durOf(x))});
$("pQueue").addEventListener("click",()=>{$("qSheet").hidden=!$("qSheet").hidden;if(!$("qSheet").hidden)$("qClose").focus()});
$("qClose").addEventListener("click",()=>{$("qSheet").hidden=true;$("pQueue").focus()});
$("qClear").addEventListener("click",()=>{P.q=P.cur!=null?[P.cur]:[];ui();persist()});
$("qList").addEventListener("click",e=>{const a=e.target.closest("[data-qp]"),r=e.target.closest("[data-qr]");
 if(a)play(+a.dataset.qp,{fromQueue:true});
 if(r){const id=+r.dataset.qr;P.q=P.q.filter(v=>v!==id);ui();persist()}});

/* driving mode: one screen, wake lock keeps the display on */
let wl=null;
async function drive(on){$("drive").hidden=!on;document.body.style.overflow=on?"hidden":"";
 if(on){if(P.cur==null&&P.q.length)play(P.q[0],{fromQueue:true});ui();$("dPlay").focus();try{wl=await navigator.wakeLock.request("screen")}catch(e){}}
 else{try{wl&&wl.release()}catch(e){}wl=null;$("pDrive").focus()}}
$("pDrive").addEventListener("click",()=>drive(true));$("dExit").addEventListener("click",()=>drive(false));

/* video: YouTube embed in a modal; pauses the audio and starts where you stopped */
function openVideo(id){const x=S[id];if(P.playing)toggle();hideDock();
 $("vFrame").innerHTML=`<iframe src="https://www.youtube-nocookie.com/embed/${x.v}?autoplay=1&start=${Math.floor(P.pos[K(x)]||0)}" title="${esc(x.t)}" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>`;
 $("vT").textContent=x.t;$("vYt").href=`https://www.youtube.com/watch?v=${x.v}`;$("vModal").hidden=false;$("vClose").focus()}
function closeVideo(){$("vModal").hidden=true;$("vFrame").innerHTML=""}
$("vClose").addEventListener("click",closeVideo);$("vModal").addEventListener("click",e=>{if(e.target.id==="vModal")closeVideo()});

/* ---------- the dial: every yeshiva is a station, north to south ---------- */
const STATIONS=REG.flatMap(g=>D.yeshivot.filter(y=>y.reg===g).sort((a,b)=>(S.some(s=>s.y===b.id)?1:0)-(S.some(s=>s.y===a.id)?1:0)));
let tuned=null;try{tuned=localStorage.getItem("osh-tuned")}catch(e){}
if(!Y[tuned]||!withData.includes(tuned))tuned=withData.slice().sort((a,b)=>S.filter(s=>s.y===b).length-S.filter(s=>s.y===a).length)[0];
function renderDial(){
 $("dial").innerHTML=STATIONS.map(y=>{const n=S.filter(s=>s.y===y.id).length;
  return `<button class="st${n?" live":""}" role="option" data-st="${y.id}" aria-selected="${y.id===tuned}" aria-current="${y.id===tuned}" aria-label="${esc(y.n)}${n?`, ${n} שיעורים`:", בקרוב"}"><span class="ticks" aria-hidden="true"></span><b>${esc(short(y.n))}</b><small>${n?`${n} שיעורים`:esc(y.reg)}</small></button>`}).join("")}
function center(id,smooth){const b=$("dial").querySelector(`[data-st="${id}"]`);if(b)b.scrollIntoView({behavior:smooth&&!document.documentElement.classList.contains("still")?"smooth":"auto",inline:"center",block:"nearest"})}
function tune(id,smooth=true){if(!Y[id])return;tuned=id;try{localStorage.setItem("osh-tuned",id)}catch(e){}
 $("dial").querySelectorAll(".st").forEach(b=>{const on=b.dataset.st===id;b.setAttribute("aria-current",on);b.setAttribute("aria-selected",on)});
 center(id,smooth);renderOnair()}
function latest(id){return S.filter(s=>s.y===id).sort((a,b)=>(b.a?1:0)-(a.a?1:0)||byNew(a,b))[0]}
function renderOnair(){const y=Y[tuned];if(!y)return;const n=S.filter(s=>s.y===y.id).length,x=n?latest(y.id):null,ch=CH[y.id];
 const playingHere=x&&P.cur!=null&&S[P.cur].y===y.id&&P.playing;
 $("onair").innerHTML=`<div><span class="lbl"><i></i>${n?"משדרים עכשיו":"התחנה בהכנה"}</span>
  <h2>ישיבת ${esc(y.n)}</h2><div class="heads">${esc(y.heads||y.reg)}</div>
  ${x?`<div class="now">${esc(x.t)}<span>${esc(x.r)}${x.d?`, ${x.d} דקות`:""}, ${esc(when(x))}</span></div>`:`<div class="now"><span>השיעורים של הישיבה עוד לא חוברו לאתר.${ch&&ch.youtube?" ערוץ היוטיוב שלה כבר זוהה.":""}</span></div>`}</div>
  <div class="acts">${x?`<button class="bigplay" data-air="${y.id}">${playingHere?PAUSE:PLAY}${playingHere?"השהיה":"האזנה לתחנה"}</button><button class="ghostw" data-airlist="${y.id}">כל ${n} השיעורים</button>`:`<a class="ghostw" style="display:inline-flex;align-items:center;text-decoration:none" href="${hesder(y)}" target="_blank" rel="noopener">לדף הישיבה באיגוד</a>`}</div>`}
$("dial").addEventListener("click",e=>{const b=e.target.closest("[data-st]");if(b)tune(b.dataset.st)});
let dt;$("dial").addEventListener("scroll",()=>{clearTimeout(dt);dt=setTimeout(()=>{const d=$("dial"),r=d.getBoundingClientRect(),mid=r.left+r.width/2;let best=null,bd=1e9;
 d.querySelectorAll(".st").forEach(b=>{const br=b.getBoundingClientRect(),dd=Math.abs(br.left+br.width/2-mid);if(dd<bd){bd=dd;best=b}});
 if(best&&best.dataset.st!==tuned){tuned=best.dataset.st;try{localStorage.setItem("osh-tuned",tuned)}catch(e){}
  d.querySelectorAll(".st").forEach(b=>{const on=b===best;b.setAttribute("aria-current",on);b.setAttribute("aria-selected",on)});renderOnair()}},140)},{passive:true});
const stepDial=d=>{const i=STATIONS.findIndex(y=>y.id===tuned);const n=STATIONS[Math.max(0,Math.min(STATIONS.length-1,i+d))];tune(n.id)};
$("dialPrev").addEventListener("click",()=>stepDial(-1));$("dialNext").addEventListener("click",()=>stepDial(1));
$("dial").addEventListener("keydown",e=>{if(e.key==="ArrowLeft"){e.preventDefault();stepDial(1)}if(e.key==="ArrowRight"){e.preventDefault();stepDial(-1)}});
$("onair").addEventListener("click",e=>{const a=e.target.closest("[data-air]"),l=e.target.closest("[data-airlist]");
 if(a){const id=a.dataset.air;if(P.cur!=null&&S[P.cur].y===id){toggle();return}
  const list=S.filter(s=>s.y===id).sort((x,y)=>(y.a?1:0)-(x.a?1:0)||byNew(x,y));P.q=list.map(x=>x.id);P.cur=null;play(P.q[0],{fromQueue:true})}
 if(l){clearAll();st.ys=[l.dataset.airlist];all();$("results").scrollIntoView({behavior:"smooth"});$("results").focus({preventScroll:true})}});

/* ---------- playlist ---------- */
let shown=25;
function renderList(){
 const r=S.filter(x=>match(x)).sort(SORTS[st.sort]);
 $("count").textContent=r.length===1?"שיעור אחד":`${r.length} שיעורים`;
 $("list").innerHTML=r.length?r.slice(0,shown).map(x=>{const y=Y[x.y],on=P.cur===x.id,inq=P.q.includes(x.id);return `<li class="shiur${on?" on":""}" data-id="${x.id}">
  <button class="pbig" data-play="${x.id}" aria-pressed="${on}" aria-label="${on&&P.playing?"השהיה":"האזנה"}: ${esc(x.t)}">${on&&P.playing?PAUSE:PLAY}</button>
  <div><h3>${esc(x.t)}</h3>
   <div class="meta"><b>${esc(x.r)}</b><span>ישיבת ${esc(short(y.n))}</span><span class="tag">${esc(x.c)}</span><span class="kind ${x.a?"ka":"kv"}">${x.a?"שמע":"וידאו בלבד"}</span><span class="nw">${esc(when(x))}</span>${resumeLabel(x)}</div></div>
  <div class="side">${x.d?`<span class="dur">${x.d}<small>דקות</small></span>`:""}
   <button class="ico" data-q="${x.id}" aria-pressed="${inq}" aria-label="${inq?"הסרה מהתור":"הוספה לתור"}">${inq?QON:QADD}</button>
   ${x.v?`<button class="ico" data-video="${x.id}" aria-label="צפייה בווידאו: ${esc(x.t)}">${VID}</button>`:""}</div></li>`}).join("")
  +(r.length>shown?`<li class="more"><button class="ghost" data-more>עוד ${Math.min(25,r.length-shown)} שיעורים</button></li>`:"")
 :`<li class="empty"><p><b>אין שיעורים שמתאימים לסינון הזה.</b></p><p>אפשר להסיר אחד מהסינונים או לחפש מילה אחרת.</p><button class="link" data-clear>ניקוי כל הסינונים</button></li>`;
 const PL=[];
 if(st.q)PL.push(["q","",`חיפוש: ${st.q}`]);
 if(st.topic)PL.push(["topic","",st.topic]);
 st.rg.forEach(k=>PL.push(["rg",k,k]));
 st.ys.forEach(k=>PL.push(["ys",k,short(Y[k].n)]));
 if(st.r)PL.push(["r","",st.r]);
 st.len.forEach(k=>PL.push(["len",k,L.find(l=>l[0]===k)[1]]));
 if(st.ao)PL.push(["ao","","רק שמע"]);
 $("pills").innerHTML=PL.map(p=>`<button class="pill" data-k="${p[0]}" data-v="${esc(p[1])}" aria-label="הסרת הסינון ${esc(p[2])}">${esc(p[2])}<span aria-hidden="true">×</span></button>`).join("")+(PL.length>1?`<button class="link" data-clear>ניקוי הכל</button>`:"");
 const n=st.ys.length+st.rg.length+st.len.length+(st.r?1:0);
 $("fcount").textContent=n?`(${n})`:"";}
const all=()=>{shown=25;renderFilters();renderList();save()};
function clearAll(){Object.assign(st,{q:"",topic:"",ys:[],rg:[],r:"",len:[],ao:false});$("q").value="";all()}
$("q").value=st.q;
let qt;$("q").addEventListener("input",e=>{clearTimeout(qt);qt=setTimeout(()=>{st.q=e.target.value.trim();all()},150)});
$("sform").addEventListener("submit",e=>{e.preventDefault();$("results").scrollIntoView({behavior:"smooth"});$("results").focus({preventScroll:true})});
$("chips").addEventListener("click",e=>{const b=e.target.closest(".chip");if(!b)return;st.topic=b.dataset.t;all()});
$("filters").addEventListener("change",e=>{const t=e.target;
 if(t.id==="fr")st.r=t.value;
 else if(t.name==="ao")st.ao=t.checked;
 else{const k={y:"ys",rg:"rg",len:"len"}[t.name];if(!k)return;st[k]=t.checked?[...st[k],t.value]:st[k].filter(v=>v!==t.value)}
 all();const el=t.id==="fr"?$("fr"):document.querySelector(`#filters input[name="${t.name}"][value="${CSS.escape(t.value)}"]`);el&&el.focus()});
$("sort").addEventListener("change",e=>{st.sort=e.target.value;renderList();save()});
$("pills").addEventListener("click",e=>{const b=e.target.closest("[data-k],[data-clear]");if(!b)return;
 if(b.dataset.clear!==undefined)return clearAll();
 const k=b.dataset.k,v=b.dataset.v;if(Array.isArray(st[k]))st[k]=st[k].filter(x=>x!==v);else if(k==="ao")st.ao=false;else st[k]="";
 if(k==="q")$("q").value="";all()});
$("list").addEventListener("click",e=>{if(e.target.closest("[data-clear]"))return clearAll();if(e.target.closest("[data-more]")){shown+=25;renderList();return}
 const p=e.target.closest("[data-play]"),q=e.target.closest("[data-q]"),v=e.target.closest("[data-video]");
 if(p)play(+p.dataset.play);
 if(q){const id=+q.dataset.q;P.q=P.q.includes(id)?P.q.filter(x=>x!==id):[...P.q,id];ui();persist()}
 if(v)openVideo(+v.dataset.video)});
$("playAll").addEventListener("click",()=>{const r=S.filter(x=>match(x)).sort(SORTS[st.sort]);if(!r.length)return;P.q=r.map(x=>x.id);P.cur=null;play(P.q[0],{fromQueue:true})});
$("clear2").addEventListener("click",clearAll);
const setF=o=>{$("filters").classList.toggle("open",o);$("scrim").classList.toggle("on",o);$("openF").setAttribute("aria-expanded",o);if(o)$("closeF").focus()};
$("openF").addEventListener("click",()=>setF(true));$("closeF").addEventListener("click",()=>{setF(false);$("openF").focus()});$("scrim").addEventListener("click",()=>setF(false));

/* ---------- yeshivot directory ---------- */
const nCon=withData.length,nCh=Object.keys(CH).filter(k=>!k.startsWith("_")&&CH[k].youtube&&!withData.includes(k)).length;
$("ylead").textContent=`${D.yeshivot.length} ישיבות מרשימת איגוד ישיבות ההסדר, מהצפון לדרום. ${nCon} כבר משדרות באתר, ועוד ${nCh} בדרך.`;
$("srcnote").textContent=`השיעורים נמשכים מאתרי הישיבות, מערוצי היוטיוב שלהן ומארכיון מורשת הרב דרוקמן. עודכן ב-${D.updated}. הנושא והרב מתויגים אוטומטית לפי הכותרת.`;
function renderY(){
 const q=norm($("yq").value.trim());
 const ys=D.yeshivot.filter(y=>!q||norm(y.n+" "+y.heads+" "+y.reg).includes(q));
 const rank=y=>S.some(s=>s.y===y.id)?0:CH[y.id]&&CH[y.id].youtube?1:2;
 $("ygrid").innerHTML=REG.map(g=>{const rows=ys.filter(y=>y.reg===g).sort((a,b)=>rank(a)-rank(b));if(!rows.length)return"";
  return `<section class="region"><h3>${esc(g)}<small>${rows.length} ישיבות</small></h3><div class="yrows">${rows.map(y=>{
   const n=S.filter(s=>s.y===y.id).length,ch=CH[y.id],r=rank(y);
   return `<div class="yrow"><b>${esc(y.n)}</b>${y.heads?`<span class="sub">${esc(y.heads)}</span>`:""}
    <span class="yst ${r===0?"on":r===1?"ch":""}"><i></i>${r===0?`${n} שיעורים באתר`:r===1?"ערוץ זוהה, בחיבור":"בקרוב"}</span>
    <div class="links">${n?`<button data-y="${y.id}">האזנה</button><button data-tune="${y.id}">לחוגה</button>`:""}${ch&&ch.youtube?`<a href="${ytUrl(ch.youtube)}" target="_blank" rel="noopener">יוטיוב</a>`:""}${ch&&ch.site?`<a href="${ch.site}" target="_blank" rel="noopener">אתר הישיבה</a>`:""}<a href="${hesder(y)}" target="_blank" rel="noopener">באיגוד</a></div></div>`}).join("")}</div></section>`}).join("")||`<p class="empty">לא נמצאה ישיבה בשם הזה.</p>`}
$("yq").addEventListener("input",renderY);
$("ygrid").addEventListener("click",e=>{const b=e.target.closest("[data-y]"),t=e.target.closest("[data-tune]");
 if(b){clearAll();st.ys=[b.dataset.y];all();$("results").scrollIntoView();$("results").focus({preventScroll:true})}
 if(t){window.scrollTo({top:0,behavior:"smooth"});tune(t.dataset.tune)}});

/* ---------- accessibility panel ---------- */
const root=document.documentElement,A={size:0,hc:false,ul:false,still:false};
try{Object.assign(A,JSON.parse(localStorage.getItem("osh-a")||"{}"))}catch(e){}
const sizes=[100,112,125,140];
const applyA=()=>{document.body.style.fontSize=(17*sizes[A.size]/100)+"px";
 $("aSizeV").textContent=sizes[A.size]+"%";$("aSize").setAttribute("aria-pressed",A.size>0);
 [["hc","aHc"],["ul","aUl"],["still","aStill"]].forEach(([k,id])=>{root.classList.toggle(k,A[k]);$(id).setAttribute("aria-pressed",A[k])});
 try{localStorage.setItem("osh-a",JSON.stringify(A))}catch(e){}};
$("aSize").addEventListener("click",()=>{A.size=(A.size+1)%sizes.length;applyA()});
[["hc","aHc"],["ul","aUl"],["still","aStill"]].forEach(([k,id])=>$(id).addEventListener("click",()=>{A[k]=!A[k];applyA()}));
$("a11yBtn").addEventListener("click",()=>{const h=!$("a11y").hidden;$("a11y").hidden=h;$("a11yBtn").setAttribute("aria-expanded",!h);if(!h)$("aSize").focus()});

/* ---------- podcast feeds: offer the feed that matches what is on screen ---------- */
const FEEDS=D.feeds||[];
function renderPods(){
 const pick=[];const add=f=>{if(f&&!pick.includes(f))pick.push(f)};
 if(st.topic)add(FEEDS.find(f=>f.kind==="topic"&&f.key===st.topic));
 st.ys.forEach(k=>add(FEEDS.find(f=>f.kind==="yeshiva"&&f.key===k)));
 if(st.r)add(FEEDS.find(f=>f.kind==="rabbi"&&f.key===st.r));
 add(FEEDS.find(f=>f.kind==="yeshiva"&&f.key===tuned));
 add(FEEDS.find(f=>f.kind==="all"));
 FEEDS.forEach(add);
 $("podList").innerHTML=pick.length?pick.map(f=>{const bare=f.url.replace(/^https?:\/\//,"");return `<li class="pod"><div><b>${esc(f.title.split(" · ")[0])}</b><span class="count">${f.n} שיעורי שמע</span>
  <div class="links"><a href="podcast://${esc(bare)}">Apple Podcasts</a><a href="pktc://subscribe/${esc(bare)}">Pocket Casts</a><a href="overcast://x-callback-url/add?url=${encodeURIComponent(f.url)}">Overcast</a><button data-copy="${esc(f.url)}">העתקת הכתובת</button></div></div></li>`}).join("")
 :`<li class="pod"><div>הפידים ייבנו אוטומטית כשיהיו שיעורי שמע.</div></li>`}
const openPods=from=>{renderPods();$("podSheet").hidden=false;$("podClose").focus();$("podClose").dataset.from=from};
$("podBtn").addEventListener("click",()=>openPods("podBtn"));$("podTop").addEventListener("click",()=>openPods("podTop"));
$("podClose").addEventListener("click",()=>{$("podSheet").hidden=true;$($("podClose").dataset.from||"podBtn").focus()});
$("podList").addEventListener("click",async e=>{const b=e.target.closest("[data-copy]");if(!b)return;
 try{await navigator.clipboard.writeText(b.dataset.copy);b.textContent="הכתובת הועתקה"}catch(err){b.textContent=b.dataset.copy}});

document.addEventListener("keydown",e=>{
 if(e.key==="/"&&!/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)){e.preventDefault();$("q").focus()}
 if(e.key===" "&&!$("drive").hidden){e.preventDefault();toggle()}
 if(e.key==="Escape"){
  if(!$("drive").hidden)drive(false);
  if(!$("vModal").hidden)closeVideo();
  if(!$("qSheet").hidden){$("qSheet").hidden=true;$("pQueue").focus()}
  if(!$("podSheet").hidden){$("podSheet").hidden=true;$("podBtn").focus()}
  if($("filters").classList.contains("open")){setF(false);$("openF").focus()}
  if(!$("a11y").hidden){$("a11y").hidden=true;$("a11yBtn").setAttribute("aria-expanded","false");$("a11yBtn").focus()}}});

applyA();all();renderY();renderDial();ui();requestAnimationFrame(()=>center(tuned,false));
}
