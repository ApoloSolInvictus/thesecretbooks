#!/usr/bin/env python3
"""Export the public WordPress content for The Secret Books to static HTML."""

from __future__ import annotations

import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://dev-the-secret-books.pantheonsite.io"
FALLBACK_URL = "https://live-the-secret-books.pantheonsite.io"
CUSTOM_DOMAIN = "tsb.wstudio3d.com"
SITE_URL = f"https://{CUSTOM_DOMAIN}"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
ASSETS = OUT / "assets"
USER_AGENT = "TheSecretBooksStaticExporter/1.0"
SEO_IMAGE_ASSET = "assets/img/TSB4.jpeg"
AUDIO_DIR = OUT / "audio"
AUDIO_EXTENSIONS = {".mp3", ".wav"}
AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
}
LOCAL_ASSET_SOURCES = {
    "hero_bg": Path(r"C:\Users\Ronny\Desktop\Invictus\TSB1.jpg"),
    "book": Path(r"C:\Users\Ronny\Desktop\Invictus\TSB2.png"),
    "book_cover": Path(r"C:\Users\Ronny\Desktop\Invictus\TSB3.png"),
    "seo_image": Path(r"C:\Users\Ronny\Desktop\Invictus\TSB4.jpeg"),
}
PDF_OVERRIDES = {
    "jasher": "https://www.holybooks.com/wp-content/uploads/Book-of-Jasher.pdf",
}

SITE_CSS = """*{box-sizing:border-box}html{scroll-behavior:smooth;overflow-x:hidden}body{margin:0;max-width:100%;overflow-x:hidden;background:#f5f5f7;color:#1d1d1f;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Segoe UI",Roboto,Arial,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}a{color:inherit;text-decoration:none}img{max-width:100%;display:block}.site-header{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:space-between;gap:24px;padding:18px clamp(22px,4vw,72px);background:rgba(255,255,255,.86);border-bottom:1px solid rgba(0,0,0,.08);backdrop-filter:saturate(180%) blur(20px);color:#1d1d1f}.home .site-header{position:absolute;left:0;right:0;background:transparent;border:0;backdrop-filter:none;color:#f5f5f7}.brand{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:0}.brand img{width:34px;height:34px;border-radius:50%}.brand span{font-size:.94rem}.site-header nav{display:flex;align-items:center;flex-wrap:wrap;gap:22px;background:transparent}.site-header nav a{padding:0;border:0;background:transparent;color:inherit;font-size:.9rem;font-weight:600;letter-spacing:0;opacity:.82}.site-header nav a:hover{opacity:1}.hero{position:relative;min-height:100vh;display:grid;grid-template-columns:minmax(0,1fr) minmax(300px,540px);align-items:center;gap:clamp(28px,5vw,76px);padding:126px clamp(24px,6vw,96px) 74px;background:var(--hero-image) center/cover no-repeat;overflow:hidden;color:#fff}.hero-mask{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.62),rgba(0,0,0,.2) 54%,rgba(0,0,0,.38));z-index:0}.hero-copy,.hero-book{position:relative;z-index:1;min-width:0}.hero-copy{max-width:760px}.hero-logo{display:none}.hero h1,.page-hero h1,.book-reader h1,.product-copy h1{margin:0;font-size:4.8rem;line-height:.96;font-weight:700;letter-spacing:0;overflow-wrap:anywhere}.hero h1{color:#fff;text-shadow:0 18px 42px rgba(0,0,0,.48)}.hero p,.page-hero p,.book-reader p,.product-copy p{max-width:720px;margin:22px 0 0;color:rgba(255,255,255,.86);font-size:1.18rem;line-height:1.65}.hero-book{width:min(540px,42vw);justify-self:center;filter:drop-shadow(0 38px 48px rgba(0,0,0,.52));transform:translateY(14px) scale(1.1)}.hero-actions,.reader-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}.button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:11px 18px;border:1px solid rgba(29,29,31,.16);border-radius:999px;background:rgba(255,255,255,.72);color:#1d1d1f;font-weight:700;letter-spacing:0;box-shadow:0 1px 2px rgba(0,0,0,.04);transition:transform .18s ease,background .18s ease,border-color .18s ease,box-shadow .18s ease}.button:hover{transform:translateY(-1px);background:#fff;border-color:rgba(29,29,31,.28);box-shadow:0 10px 28px rgba(0,0,0,.12)}.button.primary{background:#0071e3;color:#fff;border-color:#0071e3}.button.primary:hover{background:#147ce5;border-color:#147ce5}.button.full{width:100%;margin-top:12px}.book-read{padding:92px clamp(24px,7vw,112px);background:#fff;overflow:hidden}.book-read-inner{max-width:900px;color:#1d1d1f}.book-read h2,.characters-information h2,.author-bio h2,.features-information h2,.blog-information h2,.section-heading h2{margin:0 0 16px;color:#1d1d1f;font-size:3.4rem;line-height:1.04;font-weight:700;letter-spacing:0;overflow-wrap:anywhere}.book-read p,.characters-information p,.author-bio p,.features-information p,.blog-information p{color:#515154;font-size:1.06rem;line-height:1.7}.characters-information{padding:86px clamp(24px,7vw,112px);background:#f5f5f7;overflow:hidden}.character-slide{display:grid;grid-template-columns:250px minmax(0,760px);gap:34px;align-items:center;margin-top:28px}.character-slide img{width:250px;height:250px;object-fit:cover;border-radius:8px;box-shadow:0 22px 52px rgba(0,0,0,.12)}.character-slide h3{margin:0;color:#1d1d1f;font-size:2rem;line-height:1.08;font-weight:700;letter-spacing:0;overflow-wrap:anywhere}.author-information{display:grid;grid-template-columns:minmax(260px,42%) minmax(0,1fr);min-height:500px;background:#fff;overflow:hidden}.author-photo{min-height:500px;background:var(--author-image) center/contain no-repeat #f5f5f7}.author-bio{padding:clamp(48px,7vw,104px);align-self:center;min-width:0}.features-information{padding:86px clamp(24px,7vw,112px);background:#f5f5f7;color:#1d1d1f;overflow:hidden}.feature-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:30px}.feature-box{min-height:220px;padding:26px;border:1px solid rgba(29,29,31,.08);border-radius:8px;background:#fff;box-shadow:0 18px 50px rgba(0,0,0,.06)}.feature-box h3{margin:0 0 12px;color:#1d1d1f;font-size:1.26rem;line-height:1.15}.blog-information{padding:86px clamp(24px,7vw,112px);background:#fff;overflow:hidden}.secret-three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;margin-top:26px}.section{padding:80px clamp(24px,6vw,96px);overflow:hidden}.band{background:#f5f5f7}.section-heading{display:flex;align-items:end;justify-content:space-between;gap:24px;margin-bottom:26px}.eyebrow{margin:0 0 10px;color:#6e6e73;font-size:.78rem;font-weight:800;letter-spacing:0;text-transform:uppercase}.book-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(178px,1fr));gap:18px}.book-grid.compact{grid-template-columns:repeat(auto-fit,minmax(158px,1fr))}.book-card{border:1px solid rgba(29,29,31,.08);border-radius:8px;background:#fff;overflow:hidden;box-shadow:0 14px 40px rgba(0,0,0,.06);transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}.book-card:hover{transform:translateY(-3px);border-color:rgba(0,113,227,.34);box-shadow:0 24px 60px rgba(0,0,0,.12)}.book-card a{display:grid;grid-template-rows:1fr auto;height:100%}.book-card img{width:100%;aspect-ratio:3/4;object-fit:cover;background:#e8e8ed}.book-card span{min-height:70px;padding:13px;color:#1d1d1f;font-weight:700;line-height:1.25}.centered{text-align:center;margin-top:30px}.page-hero{padding:110px clamp(24px,6vw,96px) 62px;background:#fff;border-bottom:1px solid rgba(0,0,0,.08)}.page-hero.narrow{min-height:unset}.page-hero h1,.book-reader h1,.product-copy h1{color:#1d1d1f}.page-hero p,.book-reader p,.product-copy p{color:#515154}.search-label{display:grid;gap:7px;max-width:540px;margin-top:26px}.search-label span{color:#6e6e73;font-weight:700}.search-label input{width:100%;min-height:48px;border:1px solid rgba(29,29,31,.15);border-radius:999px;background:#f5f5f7;color:#1d1d1f;padding:0 18px;font:inherit;outline:none}.search-label input:focus{border-color:#0071e3;background:#fff}.book-layout{display:grid;grid-template-columns:minmax(220px,350px) minmax(0,1fr);gap:40px;padding:58px clamp(24px,5vw,76px) 76px;background:#f5f5f7}.book-aside{position:sticky;top:96px;align-self:start}.book-cover{width:100%;border-radius:8px;border:1px solid rgba(29,29,31,.1);background:#e8e8ed;box-shadow:0 24px 60px rgba(0,0,0,.12)}.book-reader{min-width:0}.pdf-frame{width:100%;height:min(78vh,920px);margin-top:26px;border:1px solid rgba(29,29,31,.12);border-radius:8px;background:#fff}.product-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(240px,460px);align-items:center;gap:44px;padding:90px clamp(24px,6vw,96px);background:#fff}.product-image{justify-self:center;max-height:640px;filter:drop-shadow(0 28px 34px rgba(0,0,0,.18))}.product-image.phone{max-height:540px}.pdf-panel,.audio-panel{padding:0 clamp(24px,6vw,96px) 76px;background:#fff}.audio-panel audio{width:100%;max-width:760px}.site-footer{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;padding:28px clamp(24px,4vw,72px);color:#6e6e73;background:#f5f5f7;border-top:1px solid rgba(0,0,0,.08)}.site-footer p{margin:0}.site-footer a{color:#1d1d1f;font-weight:700}.hidden{display:none!important}@media (max-width:960px){.hero{grid-template-columns:1fr;min-height:unset;padding-top:112px}.hero-copy{max-width:680px}.hero-book{width:min(430px,86vw);transform:none;justify-self:start}.feature-grid,.secret-three{grid-template-columns:1fr}.book-read h2,.characters-information h2,.author-bio h2,.features-information h2,.blog-information h2,.section-heading h2{font-size:2.55rem}}@media (max-width:720px){.site-header{align-items:flex-start;flex-direction:column;gap:14px;padding:18px 22px}.site-header nav{gap:16px}.home .site-header{position:absolute}.hero{padding:132px 24px 54px;background-position:center;gap:24px}.hero h1,.page-hero h1,.book-reader h1,.product-copy h1{font-size:3rem;line-height:1}.hero p,.page-hero p,.book-reader p,.product-copy p,.book-read p,.characters-information p,.author-bio p,.features-information p,.blog-information p{font-size:1rem;line-height:1.62}.hero-actions,.reader-actions{display:grid;grid-template-columns:1fr;width:100%;max-width:330px}.button{width:100%;white-space:normal;text-align:center}.hero-book{width:min(330px,86vw)}.book-read,.characters-information,.features-information,.blog-information,.section,.product-layout,.page-hero{padding-left:24px;padding-right:24px}.book-read h2,.characters-information h2,.author-bio h2,.features-information h2,.blog-information h2,.section-heading h2{font-size:2.1rem}.book-layout,.product-layout,.author-information,.character-slide{grid-template-columns:1fr}.author-photo{min-height:330px}.author-bio{padding:46px 24px}.section-heading{display:block}.book-aside{position:static}.pdf-frame{height:68vh}.book-grid{grid-template-columns:repeat(auto-fill,minmax(138px,1fr))}.book-card span{min-height:82px}.site-footer{align-items:flex-start;flex-direction:column}}"""
SITE_CSS_OVERRIDES = """.book-title-hero{position:relative;min-height:430px;display:flex;align-items:flex-end;padding:140px clamp(24px,6vw,96px) 64px;color:#fff;overflow:hidden}.book-title-hero::before{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.76),rgba(0,0,0,.28) 58%,rgba(0,0,0,.62));z-index:0}.book-title-hero-inner{position:relative;z-index:1;max-width:820px}.book-title-hero .eyebrow{color:rgba(255,255,255,.78)}.book-title-hero h1{margin:0;font-size:clamp(3rem,7vw,6.2rem);line-height:.96;font-weight:700;letter-spacing:0;overflow-wrap:anywhere;text-shadow:0 18px 42px rgba(0,0,0,.52)}.book-title-hero p{max-width:760px;margin:20px 0 0;color:rgba(255,255,255,.86);font-size:1.08rem;line-height:1.65}.book-page .book-layout{padding-top:46px}.book-reader .eyebrow,.book-reader h1,.book-reader>p{display:none}.product-image.flipbook-cover{aspect-ratio:3/4;width:min(420px,80vw);max-height:680px;object-fit:cover;border-radius:8px;box-shadow:0 28px 60px rgba(0,0,0,.16)}@media (max-width:720px){.hero h1{font-size:2.55rem;line-height:1.04}.hero-copy{max-width:100%}.book-title-hero{min-height:360px;padding:126px 24px 48px}.book-title-hero h1{font-size:2.65rem}.book-title-hero p{font-size:1rem}}@media (max-width:390px){.hero h1{font-size:2.4rem}.site-header nav{gap:12px}.site-header nav a{font-size:.86rem}.book-title-hero h1{font-size:2.35rem}}"""
AUDIO_PLAYER_CSS = """.tsb-audio-player{position:fixed;right:18px;bottom:18px;z-index:2147483000;display:flex;align-items:center;gap:8px;padding:8px;border:1px solid rgba(255,255,255,.36);border-radius:999px;background:rgba(245,245,247,.72);box-shadow:0 18px 48px rgba(0,0,0,.18);backdrop-filter:saturate(180%) blur(22px)}.tsb-audio-player button{appearance:none;border:0;background:transparent;color:#1d1d1f;cursor:pointer}.tsb-audio-main{width:54px;height:54px;padding:0;border-radius:50%;overflow:hidden;box-shadow:0 10px 24px rgba(0,0,0,.18);transition:transform .18s ease,box-shadow .18s ease,filter .18s ease}.tsb-audio-main:hover{transform:translateY(-1px);box-shadow:0 16px 34px rgba(0,0,0,.24)}.tsb-audio-main img{width:100%;height:100%;object-fit:cover}.tsb-audio-main::after{content:"";position:absolute;inset:auto 9px 9px auto;width:13px;height:13px;border-radius:50%;background:#6e6e73;box-shadow:0 0 0 2px rgba(255,255,255,.92)}.tsb-audio-player.is-playing .tsb-audio-main::after{background:#34c759}.tsb-audio-player.is-blocked .tsb-audio-main{filter:saturate(1.18);box-shadow:0 0 0 3px rgba(0,113,227,.22),0 18px 42px rgba(0,0,0,.2)}.tsb-audio-main{position:relative}.tsb-audio-volume{display:grid;gap:4px}.tsb-audio-volume button{width:32px;height:25px;display:grid;place-items:center;border-radius:999px;background:rgba(255,255,255,.72);box-shadow:inset 0 0 0 1px rgba(29,29,31,.08)}.tsb-audio-volume button:hover{background:#fff}.tsb-audio-volume svg{width:15px;height:15px;stroke:currentColor;stroke-width:2.2;fill:none;stroke-linecap:round;stroke-linejoin:round}@media (max-width:720px){.tsb-audio-player{right:14px;bottom:14px;padding:7px}.tsb-audio-main{width:50px;height:50px}.tsb-audio-volume button{width:30px;height:24px}}"""
SITE_JS = """(()=>{const TRACKS=__TSB_AUDIO_PLAYLIST__;const script=document.currentScript||[...document.scripts].find(item=>item.src&&item.src.includes("/assets/js/site.js"));const siteRoot=new URL("../../",script&&script.src?script.src:document.baseURI);const stateKey="tsbAudioStateV1";const volumeKey="tsbAudioVolume";const plusIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';const minusIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/></svg>';let player;let audio;let currentIndex=0;let currentSource=null;let userPaused=false;let blocked=false;let saveTimer=0;function clamp(value,min,max){return Math.min(max,Math.max(min,value));}function readState(){try{return JSON.parse(sessionStorage.getItem(stateKey)||"{}")||{};}catch{return {};}}function saveState(){if(!audio||!currentSource)return;const state={index:currentIndex,src:currentSource.src,time:audio.currentTime||0,volume:audio.volume,userPaused};sessionStorage.setItem(stateKey,JSON.stringify(state));localStorage.setItem(volumeKey,String(audio.volume));}function scheduleSave(){clearTimeout(saveTimer);saveTimer=setTimeout(saveState,250);}function pickSource(track){if(!track||!track.sources||!track.sources.length)return null;return track.sources.find(source=>!source.type||audio.canPlayType(source.type))||track.sources[0];}function setPlayerState(){if(!player||!audio)return;player.classList.toggle("is-playing",!audio.paused&&!audio.ended);player.classList.toggle("is-blocked",blocked&&audio.paused&&!userPaused);}function requestPlay(){if(!audio||!currentSource)return;blocked=false;const promise=audio.play();if(promise&&typeof promise.then==="function"){promise.then(()=>{blocked=false;setPlayerState();saveState();}).catch(()=>{blocked=true;setPlayerState();});}else{setPlayerState();}return promise;}function loadTrack(index,options={}){if(!TRACKS.length||!audio)return;currentIndex=(index+TRACKS.length)%TRACKS.length;currentSource=pickSource(TRACKS[currentIndex]);if(!currentSource)return;const nextUrl=new URL(currentSource.src,siteRoot).href;if(audio.src!==nextUrl){audio.src=nextUrl;audio.load();}const resumeTime=Number(options.time||0);if(resumeTime>0){const applyTime=()=>{try{if(Number.isFinite(audio.duration)&&resumeTime<audio.duration-1)audio.currentTime=resumeTime;}catch{}};if(audio.readyState>=1)applyTime();else audio.addEventListener("loadedmetadata",applyTime,{once:true});}if(!userPaused)requestPlay();setPlayerState();}function nextTrack(){loadTrack(currentIndex+1,{time:0});}function changeVolume(delta){if(!audio)return;audio.volume=clamp(Math.round((audio.volume+delta)*10)/10,0,1);scheduleSave();setPlayerState();}function buildPlayer(){if(!TRACKS.length||document.querySelector("[data-tsb-audio-player]"))return;const state=readState();currentIndex=Number.isInteger(state.index)&&state.index>=0&&state.index<TRACKS.length?state.index:0;userPaused=state.userPaused===true;audio=document.createElement("audio");audio.preload="auto";const savedVolume=Number(localStorage.getItem(volumeKey));audio.volume=Number.isFinite(state.volume)?clamp(state.volume,0,1):Number.isFinite(savedVolume)?clamp(savedVolume,0,1):0.72;player=document.createElement("div");player.className="tsb-audio-player";player.dataset.tsbAudioPlayer="";const main=document.createElement("button");main.className="tsb-audio-main";main.type="button";main.setAttribute("aria-label","Play or pause audio");const logo=document.createElement("img");logo.src=new URL("assets/img/TSB-Logo-App-250x250.png",siteRoot).href;logo.alt="";main.append(logo);const volume=document.createElement("div");volume.className="tsb-audio-volume";const up=document.createElement("button");up.type="button";up.setAttribute("aria-label","Volume up");up.innerHTML=plusIcon;const down=document.createElement("button");down.type="button";down.setAttribute("aria-label","Volume down");down.innerHTML=minusIcon;volume.append(up,down);player.append(audio,main,volume);document.body.append(player);main.addEventListener("click",()=>{if(audio.paused){userPaused=false;loadTrack(currentIndex,{time:audio.currentTime||0});}else{userPaused=true;audio.pause();saveState();setPlayerState();}});up.addEventListener("click",event=>{event.stopPropagation();changeVolume(.1);if(audio.paused&&!userPaused)requestPlay();});down.addEventListener("click",event=>{event.stopPropagation();changeVolume(-.1);});audio.addEventListener("play",()=>{blocked=false;setPlayerState();saveState();});audio.addEventListener("pause",()=>{setPlayerState();saveState();});audio.addEventListener("timeupdate",scheduleSave);audio.addEventListener("volumechange",scheduleSave);audio.addEventListener("ended",nextTrack);audio.addEventListener("error",()=>{setTimeout(nextTrack,700);});window.addEventListener("pagehide",saveState);document.addEventListener("pointerdown",()=>{if(blocked&&!userPaused)requestPlay();},{once:true,capture:true});const track=TRACKS[currentIndex];const source=track?pickSource(track):null;const resumeTime=source&&state.src===source.src?Number(state.time||0):0;loadTrack(currentIndex,{time:resumeTime});}function initBookSearch(root=document){const input=root.querySelector("[data-book-search]");const grid=root.querySelector("[data-book-grid]");if(!input||!grid||input.dataset.searchReady)return;input.dataset.searchReady="1";const cards=[...grid.querySelectorAll(".book-card")];input.addEventListener("input",()=>{const q=input.value.trim().toLowerCase();cards.forEach(card=>{card.classList.toggle("hidden",q&&!card.dataset.title.includes(q));});});}function navigableUrl(anchor,event){if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return null;if(anchor.target&&anchor.target!=="_self")return null;if(anchor.hasAttribute("download"))return null;const href=anchor.getAttribute("href");if(!href||href.startsWith("#")||href.startsWith("mailto:")||href.startsWith("tel:"))return null;const url=new URL(href,location.href);if(url.origin!==location.origin)return null;if(url.hash&&url.pathname===location.pathname)return null;if(url.pathname.includes("/assets/")||url.pathname.includes("/audio/"))return null;const file=url.pathname.split("/").pop()||"";const ext=file.includes(".")?file.slice(file.lastIndexOf(".")).toLowerCase():"";if(ext&&ext!==".html")return null;return url;}function replaceFrom(nextDoc,selector){const current=document.querySelector(selector);const next=nextDoc.querySelector(selector);if(current&&next)current.replaceWith(document.importNode(next,true));}async function navigate(url,push=true){try{saveState();const response=await fetch(url.href,{credentials:"same-origin"});if(!response.ok)throw new Error("navigation failed");const html=await response.text();const nextDoc=new DOMParser().parseFromString(html,"text/html");if(!nextDoc.querySelector("main"))throw new Error("missing main");if(push)history.pushState({tsb:true},"",url.href);document.title=nextDoc.title;document.body.className=nextDoc.body.className;replaceFrom(nextDoc,"header.site-header");replaceFrom(nextDoc,"main");replaceFrom(nextDoc,"footer.site-footer");initBookSearch(document);window.scrollTo(0,0);}catch{location.href=url.href;}}function initNavigation(){document.addEventListener("click",event=>{const anchor=event.target.closest&&event.target.closest("a[href]");if(!anchor)return;const url=navigableUrl(anchor,event);if(!url)return;event.preventDefault();navigate(url,true);});window.addEventListener("popstate",()=>navigate(new URL(location.href),false));}function init(){initBookSearch(document);buildPlayer();initNavigation();}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();})();"""


@dataclass
class Book:
    id: int
    slug: str
    title: str
    excerpt: str
    pdf_url: str
    pdf_asset: str
    cover_url: str
    cover_asset: str
    original_url: str
    source_site: str
    pdf_note: str


def request_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=90) as response:
        return response.read()


def request_json(url: str) -> Any:
    return json.loads(request_bytes(url).decode("utf-8"))


def wp_json(path: str, base_url: str = BASE_URL) -> Any:
    return request_json(f"{base_url}/{path.lstrip('/')}")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def escape(value: str) -> str:
    return html.escape(value or "", quote=True)


def slugify_file(name: str) -> str:
    name = unquote(name).strip()
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "asset"


def asset_name_for(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return slugify_file(name)


def normalize_wp_asset_url(url: str, source_site: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    source_host = urlparse(source_site).netloc
    if "/wp-content/uploads/" in parsed.path and parsed.netloc and parsed.netloc != source_host:
        return f"{source_site.rstrip('/')}{parsed.path}"
    return url


def download_asset(url: str, subdir: str) -> str:
    if not url:
        return ""

    asset_dir = ASSETS / subdir
    asset_dir.mkdir(parents=True, exist_ok=True)
    name = asset_name_for(url)
    dest = asset_dir / name

    if not dest.exists() or dest.stat().st_size == 0:
        print(f"download {subdir}/{name}")
        try:
            dest.write_bytes(request_bytes(url))
        except Exception as exc:  # noqa: BLE001
            print(f"warning: could not download {url}: {exc}")
            return url

    return f"assets/{subdir}/{name}".replace("\\", "/")


def copy_local_asset(path: Path, subdir: str) -> str:
    if not path.exists():
        print(f"warning: local asset not found: {path}")
        return ""

    asset_dir = ASSETS / subdir
    asset_dir.mkdir(parents=True, exist_ok=True)
    dest = asset_dir / path.name
    if not dest.exists() or dest.stat().st_size != path.stat().st_size:
        print(f"copy {subdir}/{path.name}")
        shutil.copy2(path, dest)

    return f"assets/{subdir}/{path.name}".replace("\\", "/")


def rel(path: str, depth: int) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return "../" * depth + path


def extract_pdf(content: str) -> str:
    content = content.replace("\\/", "/")
    match = re.search(r'"source"\s*:\s*"([^"]+?\.pdf)"', content, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"https://[^\"'\s<>]+?\.pdf", content, re.IGNORECASE)
    return match.group(0) if match else ""


def extract_thumb(content: str) -> str:
    match = re.search(r'\bthumb="([^"]+)"', content)
    return match.group(1) if match else ""


def page_start(title: str, depth: int = 0, body_class: str = "") -> str:
    css = rel("assets/css/styles.css", depth)
    js = rel("assets/js/site.js", depth)
    icon = rel("assets/img/TSB-Logo-App-50x50.png", depth)
    page_title = f"{title} - The Secret Books"
    description = "The Secret Books is a clean digital library of apocryphal, lost, and hidden biblical writings."
    seo_image = f"{SITE_URL}/{SEO_IMAGE_ASSET}"
    nav = [
        ("Home", rel("index.html", depth)),
        ("Books", rel("books/index.html", depth)),
        ("iBook", rel("ibook/index.html", depth)),
        ("App", rel("secret-app/index.html", depth)),
    ]
    nav_html = "\n".join(f'<a href="{href}">{label}</a>' for label, href in nav)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(page_title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="The Secret Books">
  <meta property="og:title" content="{escape(page_title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:image" content="{seo_image}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(page_title)}">
  <meta name="twitter:description" content="{escape(description)}">
  <meta name="twitter:image" content="{seo_image}">
  <link rel="icon" href="{icon}">
  <link rel="apple-touch-icon" href="{rel('assets/img/TSB-Logo-App-250x250.png', depth)}">
  <link rel="stylesheet" href="{css}">
  <script defer src="{js}"></script>
</head>
<body class="{escape(body_class)}">
  <header class="site-header">
    <a class="brand" href="{rel('index.html', depth)}">
      <img src="{rel('assets/img/TSB-Logo-App-250x250.png', depth)}" alt="">
      <span>The Secret Books</span>
    </a>
    <nav aria-label="Primary navigation">
      {nav_html}
    </nav>
  </header>
"""


def page_end(depth: int = 0) -> str:
    return f"""
  <footer class="site-footer">
    <p>The Secret Books. Ancient wisdom gathered for the present and the future.</p>
    <a href="{rel('books/index.html', depth)}">Explore the Library</a>
  </footer>
</body>
</html>
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def book_card(book: Book, depth: int = 0) -> str:
    cover = rel(book.cover_asset, depth)
    href = rel(f"{book.slug}/index.html", depth)
    return f"""
      <article class="book-card" data-title="{escape(book.title.lower())}">
        <a href="{href}">
          <img src="{cover}" alt="">
          <span>{escape(book.title)}</span>
        </a>
      </article>
"""


def render_home(books: list[Book], assets: dict[str, str]) -> str:
    featured = books[-8:][::-1]
    cards = "".join(book_card(book, 0) for book in featured)
    hero_bg = rel(assets["hero_bg"], 0)
    book = rel(assets["book"], 0)
    read_bg = rel(assets["read_bg"], 0)
    character_bg = rel(assets["character_bg"], 0)
    character_img = rel(assets["character_img"], 0)
    moon_bg = rel(assets["moon_bg"], 0)
    return page_start("Discover", 0, "home") + f"""
  <main>
    <section class="hero" style="background: url('{hero_bg}') center/cover no-repeat">
      <div class="hero-mask"></div>
      <div class="hero-copy">
        <h1>The Secret Books</h1>
        <p>Ancient writings, apocrypha, visions, gospels, epistles, and hidden histories gathered into one quiet library.</p>
        <div class="hero-actions">
          <a class="button primary" href="books/index.html">Enter the Library</a>
          <a class="button" href="ibook/index.html">Open iBook</a>
        </div>
      </div>
      <img class="hero-book" src="{book}" alt="">
    </section>

    <section class="book-read" style="--read-image: url('{read_bg}')">
      <div class="book-read-inner">
        <p class="eyebrow">The Secret History</p>
        <h2>Why These Books Are Secret?</h2>
        <p>Once upon a time, in the ancient lands of the Near East, a new faith was emerging: Christianity. In those early years, many different texts circulated among the followers of Jesus, each offering a unique glimpse into the life and teachings of the man from Nazareth. Some of these texts were embraced by the early Christians, while others were considered too radical or too unorthodox for mainstream acceptance.</p>
        <div class="hero-actions">
          <a class="button primary" href="ibook/index.html">Open iBook</a>
          <a class="button" href="books/index.html">Read &amp; Explore the Books</a>
        </div>
      </div>
    </section>

    <section class="characters-information" style="--character-image: url('{character_bg}')">
      <h2>Meet the Books</h2>
      <div class="character-slide">
        <img src="{character_img}" alt="">
        <div>
          <p class="eyebrow">Prologue</p>
          <h3>Hidden words for the wise</h3>
          <p>In Daniel 12:9-10 we hear of words that are shut up until the end of time, words that the wise shall understand and the wicked shall not. In 4 Ezra 14:44ff. there are 94 books: 24 to be published and 70 to be delivered only to the wise among the people.</p>
        </div>
      </div>
    </section>

    <section class="author-information">
      <div class="author-photo" style="background: url('{book}') center/contain no-repeat #f5f5f7"></div>
      <div class="author-bio">
        <p class="eyebrow">The Secret Books</p>
        <h2>These books are part of our history, and they should be studied.</h2>
        <p>For centuries, the Bible has been considered the definitive source of knowledge and truth for billions of people. But what if there were books left out of this holy text? The Secret Books dives into hidden history, forgotten stories, mysterious figures, and ancient wisdom.</p>
      </div>
    </section>

    <section class="features-information" style="--moon-image: url('{moon_bg}')">
      <h2>About The Secret Books</h2>
      <div class="feature-grid">
        <article class="feature-box">
          <h3>All Digital</h3>
          <p>Part of the new era is to be ecological and easy to access, so ancient wisdom can remain available for the present and the future.</p>
        </article>
        <article class="feature-box">
          <h3>Mystery</h3>
          <p>Uncover the mysteries of the past and open your mind to old wisdom that shows another view of the world.</p>
        </article>
        <article class="feature-box">
          <h3>Full of Love</h3>
          <p>These books speak about love for the Creator and the living connection found in teachings from prophets of the past.</p>
        </article>
      </div>
    </section>

    <section class="blog-information">
      <h2>Three Books Of Secrets</h2>
      <div class="secret-three">
        {''.join(book_card(book, 0) for book in featured[:3])}
      </div>
    </section>

    <section class="section band">
      <div class="section-heading">
        <p class="eyebrow">Library</p>
        <h2>{len(books)} books gathered</h2>
      </div>
      <div class="book-grid compact">
        {cards}
      </div>
      <div class="centered">
        <a class="button primary" href="books/index.html">View All Books</a>
      </div>
    </section>
  </main>
""" + page_end(0)


def render_books_index(books: list[Book]) -> str:
    cards = "".join(book_card(book, 1) for book in books)
    return page_start("Books", 1, "library") + f"""
  <main>
    <section class="page-hero narrow">
      <p class="eyebrow">Books</p>
      <h1>The Library</h1>
      <p>{len(books)} books are available with readable PDF editions, covers, and direct downloads.</p>
      <label class="search-label">
        <span>Search</span>
        <input type="search" data-book-search placeholder="Search books">
      </label>
    </section>
    <section class="section">
      <div class="book-grid" data-book-grid>
        {cards}
      </div>
    </section>
  </main>
""" + page_end(1)


def render_book(book: Book, previous_book: Book | None, next_book: Book | None) -> str:
    cover = rel(book.cover_asset, 1)
    pdf = rel(book.pdf_asset, 1)
    prev_link = (
        f'<a class="button" href="../{previous_book.slug}/index.html">Previous</a>'
        if previous_book
        else ""
    )
    next_link = (
        f'<a class="button" href="../{next_book.slug}/index.html">Next</a>'
        if next_book
        else ""
    )
    return page_start(book.title, 1, "book-page") + f"""
  <main>
    <section class="book-title-hero" style="background: url('{cover}') center/cover no-repeat">
      <div class="book-title-hero-inner">
        <p class="eyebrow">The Secret Books</p>
        <h1>{escape(book.title)}</h1>
        <p>{escape(book.excerpt or "Read the preserved PDF edition in the library.")}</p>
      </div>
    </section>
    <article class="book-layout">
      <aside class="book-aside">
        <img class="book-cover" src="{cover}" alt="">
        <a class="button primary full" href="{pdf}" download>Download PDF</a>
      </aside>
      <section class="book-reader">
        <p class="eyebrow">The Secret Books</p>
        <h1>{escape(book.title)}</h1>
        <p>{escape(book.excerpt or "Read the preserved PDF edition in the static library.")}</p>
        <div class="reader-actions">
          {prev_link}
          <a class="button" href="../books/index.html">All Books</a>
          {next_link}
        </div>
        <iframe class="pdf-frame" title="{escape(book.title)} PDF" src="{pdf}"></iframe>
      </section>
    </article>
  </main>
""" + page_end(1)


def render_ibook(assets: dict[str, str]) -> str:
    pdf = rel(assets["ibook_pdf"], 1)
    image = rel(assets.get("book_cover") or assets["ibook_img"], 1)
    return page_start("iBook", 1, "product-page") + f"""
  <main>
    <section class="product-layout">
      <div class="product-copy">
        <p class="eyebrow">iBook</p>
        <h1>The Secret iBook</h1>
        <p>A visual companion edition for entering the ancient stories with a cinematic sense of place and time.</p>
        <a class="button primary" href="{pdf}" download>Download iBook PDF</a>
      </div>
      <img class="product-image flipbook-cover" src="{image}" alt="">
    </section>
    <section class="pdf-panel">
      <iframe class="pdf-frame" title="The Secret iBook PDF" src="{pdf}"></iframe>
    </section>
  </main>
""" + page_end(1)


def render_app(assets: dict[str, str], audio_asset: str) -> str:
    app_img = rel(assets["app_img"], 1)
    audio = rel(audio_asset, 1)
    return page_start("Secret App", 1, "product-page") + f"""
  <main>
    <section class="product-layout">
      <div class="product-copy">
        <p class="eyebrow">App</p>
        <h1>Secret App</h1>
        <p>The mobile companion for The Secret Books, gathered here with a cinematic audio asset for contemplation and study.</p>
        <div class="hero-actions">
          <a class="button primary" href="../books/index.html">Browse Books</a>
          <a class="button" href="{audio}" download>Download Audio</a>
        </div>
      </div>
      <img class="product-image phone" src="{app_img}" alt="">
    </section>
    <section class="audio-panel">
      <h2>Audiobook Asset</h2>
      <audio controls src="{audio}"></audio>
    </section>
  </main>
""" + page_end(1)


def render_placeholder(title: str, message: str, depth: int = 1) -> str:
    return page_start(title, depth, "status-page") + f"""
  <main>
    <section class="page-hero narrow">
      <p class="eyebrow">The Secret Books</p>
      <h1>{escape(title)}</h1>
      <p>{escape(message)}</p>
      <a class="button primary" href="{rel('books/index.html', depth)}">Return to Books</a>
    </section>
  </main>
""" + page_end(depth)


def fetch_all(endpoint: str, base_url: str = BASE_URL, per_page: int = 100) -> list[Any]:
    first_url = f"{base_url}/{endpoint.lstrip('/')}?per_page={per_page}"
    if "?" in endpoint:
        first_url = f"{base_url}/{endpoint.lstrip('/')}&per_page={per_page}"
    req = Request(first_url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=90) as response:
        total_pages = int(response.headers.get("X-WP-TotalPages", "1") or "1")

    sep = "&" if "?" in endpoint else "?"
    items: list[Any] = []
    for page in range(1, total_pages + 1):
        items.extend(wp_json(f"{endpoint}{sep}per_page={per_page}&page={page}", base_url))
    return items


def collect_books() -> list[Book]:
    fields = "_fields=id,slug,link,title,content,excerpt,featured_media&orderby=date&order=asc"
    primary_posts = fetch_all(f"wp-json/wp/v2/posts?{fields}", BASE_URL)
    fallback_posts = fetch_all(f"wp-json/wp/v2/posts?{fields}", FALLBACK_URL)
    posts_by_slug: dict[str, tuple[dict[str, Any], str]] = {
        post["slug"]: (post, BASE_URL) for post in primary_posts
    }
    for post in fallback_posts:
        posts_by_slug.setdefault(post["slug"], (post, FALLBACK_URL))

    primary_media = fetch_all(
        "wp-json/wp/v2/media?_fields=id,source_url,media_type,mime_type,title",
        BASE_URL,
    )
    fallback_media = fetch_all(
        "wp-json/wp/v2/media?_fields=id,source_url,media_type,mime_type,title",
        FALLBACK_URL,
    )
    media_by_source = {
        BASE_URL: {item["id"]: item for item in primary_media},
        FALLBACK_URL: {item["id"]: item for item in fallback_media},
    }

    books: list[Book] = []
    ordered_posts = sorted(posts_by_slug.values(), key=lambda item: item[0]["id"])
    for post, source_site in ordered_posts:
        content = post["content"]["rendered"]
        title = clean_text(post["title"]["rendered"])
        pdf_note = ""
        pdf_url = normalize_wp_asset_url(extract_pdf(content), source_site)
        if post["slug"] in PDF_OVERRIDES:
            pdf_url = PDF_OVERRIDES[post["slug"]]
            pdf_note = "Pantheon public post pointed to Baruch.pdf; exported with a public Book of Jasher PDF override."
        thumb_url = normalize_wp_asset_url(extract_thumb(content), source_site)
        featured = media_by_source[source_site].get(post.get("featured_media"))
        cover_url = normalize_wp_asset_url((featured or {}).get("source_url") or thumb_url, source_site)
        excerpt = clean_text(post.get("excerpt", {}).get("rendered", ""))

        books.append(
            Book(
                id=post["id"],
                slug=post["slug"],
                title=title,
                excerpt=excerpt,
                pdf_url=pdf_url,
                pdf_asset=download_asset(pdf_url, "pdfs"),
                cover_url=cover_url,
                cover_asset=download_asset(cover_url, "img/covers"),
                original_url=post["link"],
                source_site=source_site,
                pdf_note=pdf_note,
            )
        )

    return books


def collect_site_assets() -> tuple[dict[str, str], str]:
    urls = {
        "logo": f"{BASE_URL}/wp-content/uploads/2024/05/TSB-Logo.png",
        "app_icon": f"{BASE_URL}/wp-content/uploads/2024/05/TSB-Logo-App-250x250.png",
        "app_icon_small": f"{BASE_URL}/wp-content/uploads/2024/05/TSB-Logo-App-50x50.png",
        "hero_bg": f"{BASE_URL}/wp-content/uploads/2024/05/TDsekcUuGseauE7C6v5g-1-bfdnu.jpg",
        "read_bg": f"{BASE_URL}/wp-content/uploads/2024/05/ZrO7CPvnjYlVuk5Tb1OW-1-erpxv.jpg",
        "character_bg": f"{BASE_URL}/wp-content/uploads/2024/05/ztg8E5WLXIyupqfEpg12-1-g8k4n.jpg",
        "character_img": f"{BASE_URL}/wp-content/uploads/2024/05/rT5VkYTgYeoI8LuRowux-1-ps36q-250x250.jpg",
        "moon_bg": f"{BASE_URL}/wp-content/uploads/2024/05/moon-sky-night-background-asset-game-2d-futuristic-generative-ai.jpg",
        "book": f"{BASE_URL}/wp-content/uploads/2024/05/book23.png",
        "ibook_img": f"{BASE_URL}/wp-content/uploads/2024/05/ibook2.png",
        "app_img": f"{BASE_URL}/wp-content/uploads/2024/05/App1.png",
        "ibook_pdf": f"{BASE_URL}/wp-content/uploads/edd/2024/05/The-Secret-Books.pdf",
    }
    assets = {key: download_asset(url, "img" if not url.endswith(".pdf") else "pdfs") for key, url in urls.items()}
    for key, source in LOCAL_ASSET_SOURCES.items():
        assets[key] = copy_local_asset(source, "img")
    audio_url = f"{BASE_URL}/wp-content/uploads/edd/2024/06/FREE-music-Symphony-of-Specters-Intense-Cinematic-Trailer.mp3"
    audio_asset = download_asset(audio_url, "audio")
    return assets, audio_asset


def audio_title(path: Path) -> str:
    title = re.sub(r"[-_]+", " ", path.stem)
    title = re.sub(r"\s+", " ", title).strip()
    return title or path.stem


def collect_audio_playlist() -> list[dict[str, Any]]:
    tracks: dict[str, dict[str, Any]] = {}
    for directory in (AUDIO_DIR, ASSETS / "audio"):
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            key = path.stem.lower()
            rel_path = path.relative_to(OUT).as_posix()
            track = tracks.setdefault(key, {"title": audio_title(path), "sources": []})
            track["sources"].append(
                {
                    "src": rel_path,
                    "type": AUDIO_MIME_TYPES.get(path.suffix.lower(), ""),
                }
            )

    playlist = list(tracks.values())
    playlist.sort(key=lambda track: ("maximus" not in track["title"].lower(), track["title"].lower()))
    return playlist


def write_static_assets(audio_playlist: list[dict[str, Any]]) -> None:
    playlist_json = json.dumps(audio_playlist, ensure_ascii=False)
    write(ASSETS / "css" / "styles.css", SITE_CSS + SITE_CSS_OVERRIDES + AUDIO_PLAYER_CSS)
    write(
        ASSETS / "js" / "site.js",
        SITE_JS.replace("__TSB_AUDIO_PLAYLIST__", playlist_json),
    )

def main() -> None:
    if OUT.exists():
        for item in OUT.iterdir():
            if item.name in {"assets", "audio"}:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "CNAME").write_text(f"{CUSTOM_DOMAIN}\n", encoding="utf-8")

    assets, audio_asset = collect_site_assets()
    write_static_assets(collect_audio_playlist())
    books = collect_books()

    write(OUT / "index.html", render_home(books, assets))
    write(OUT / "books" / "index.html", render_books_index(books))
    write(OUT / "ibook" / "index.html", render_ibook(assets))
    write(OUT / "secret-app" / "index.html", render_app(assets, audio_asset))
    write(
        OUT / "login" / "index.html",
        render_placeholder("Login", "Account login is not required for this library edition. You can read the books directly from the archive."),
    )
    write(
        OUT / "checkout" / "index.html",
        render_placeholder("Checkout", "Checkout is not required for this library edition. The available books can be opened directly from the archive."),
    )
    write(OUT / "404.html", render_placeholder("Page Not Found", "The page was not found in this library.", 0))

    for index, book in enumerate(books):
        previous_book = books[index - 1] if index > 0 else None
        next_book = books[index + 1] if index + 1 < len(books) else None
        write(OUT / book.slug / "index.html", render_book(book, previous_book, next_book))

    inventory = {
        "source": BASE_URL,
        "fallback_source": FALLBACK_URL,
        "book_count": len(books),
        "books": [book.__dict__ for book in books],
        "notes": [
            "Pantheon Git clone requires a registered SSH public key.",
            "The dev WordPress REST API reported 46 public posts/books at export time.",
            "The static export includes any additional public books found on the live environment that are not present on dev.",
            "The Jasher post on Pantheon points to Baruch.pdf, so Jasher is exported with a public PDF override.",
            "Dynamic WordPress features such as login, checkout, BuddyPress, and EDD cart are represented as static placeholder pages.",
        ],
    }
    write(OUT / "data" / "inventory.json", json.dumps(inventory, indent=2, ensure_ascii=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
