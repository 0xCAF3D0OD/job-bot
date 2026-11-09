(()=>{
const out=[];const R=e=>e.getBoundingClientRect();const cs=e=>getComputedStyle(e);
const name=e=>(e.className&&e.className.baseVal===undefined?('.'+String(e.className).trim().split(/\s+/).join('.')):'')||e.tagName.toLowerCase();
const txt=e=>(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,28);
const cards=[...document.querySelectorAll('.s.info,.row,.ob,.btn')];
// 1. overflow inside cards
document.querySelectorAll('.s.info, .row').forEach(c=>{const cr=R(c);const bw=parseFloat(cs(c).borderRightWidth)||0;
 c.querySelectorAll('*').forEach(k=>{const r=R(k);if(r.width&&r.right>cr.right-bw+0.5)out.push({regle:'debordement',ou:name(c)+' '+txt(c),element:name(k)+' '+txt(k),px:+(r.right-cr.right+bw).toFixed(1)})})});
// viewport
document.querySelectorAll('.scroll *').forEach(k=>{const r=R(k);if(r.width&&r.right>innerWidth+0.5)out.push({regle:'hors ecran',element:name(k)+' '+txt(k)})});
// 2. trailing icons distance to card edge
const trail=[...document.querySelectorAll('.row .go, .tg .chv, .ft svg')];
trail.forEach(t=>{const c=t.closest('.s.info,.row');if(!c)return;const d=R(c).right-R(t).right;if(Math.abs(d-20)>1)out.push({regle:'icone de fin a 20 px du bord',element:name(t)+' dans '+txt(c),px:+d.toFixed(1)})});
// 3+4. note card: axis & keyline
document.querySelectorAll('.s.info').forEach(c=>{const ring=c.querySelector(':scope > div > svg, :scope > div > span');if(!ring)return;const rr=R(ring);const axis=rr.left+rr.width/2;const head=c.querySelector(':scope > div > div');const key=head?R(head).left:null;
 c.querySelectorAll('.ax').forEach(a=>{if(a.closest('.fh,.tg'))return;const s=a.querySelector('svg');if(!s)return;const r=R(s);if(!r.width)return;const cx=r.left+r.width/2;if(Math.abs(cx-axis)>1)out.push({regle:'icone sur l axe de la note',element:txt(a.parentElement),px:+(cx-axis).toFixed(1)})});
 if(key!==null)c.querySelectorAll('.tg > b:first-of-type, .cr > div').forEach(t=>{const d=R(t).left-key;if(Math.abs(d)>1)out.push({regle:'texte aligne sur le verdict',element:txt(t),px:+d.toFixed(1)})});
 const sizes=new Set([...c.querySelectorAll('.tg svg:not(.chv), .cr svg, .kid svg, .fh svg')].map(s=>Math.round(R(s).width)).filter(w=>w>0));if(sizes.size>1)out.push({regle:'une seule taille d icone',tailles:[...sizes]});
});
// 5. grid of 4 for paddings/margins/gaps (border compensated)
document.querySelectorAll('.scroll *, .top, .bar').forEach(k=>{const s=cs(k);const bw=['Top','Right','Bottom','Left'].map(x=>{const v=parseFloat(s['border'+x+'Width'])||0;return v>1?v:0});if(k.classList.contains('ft'))return;
 ['Top','Right','Bottom','Left'].forEach((side,i)=>{const p=parseFloat(s['padding'+side]);if(p&&(p%4)>0.01&&((p+bw[i])%4)>0.01&&((p+1.5)%4)>0.01)out.push({regle:'grille de 4 (padding)',element:name(k)+' '+txt(k),cote:side,px:p+bw[i]});
  const m=parseFloat(s['margin'+side]);if((Math.abs(m+14.5)<0.01||Math.abs(m+18.5)<0.01))return;if(side==='Left'&&k.getAttribute&&/margin-left:\s*auto/.test(k.getAttribute('style')||''))return;if(m&&Math.abs(m)%4>0.01&&!(k.classList.contains('ft'))&&!(k.classList&&k.classList.contains('chv')))out.push({regle:'grille de 4 (marge)',element:name(k)+' '+txt(k),cote:side,px:m})});
 const g=parseFloat(s.columnGap)||0, rg=parseFloat(s.rowGap)||0;[g,rg].forEach(v=>{if(v&&v%4>0.01)out.push({regle:'grille de 4 (gap)',element:name(k)+' '+txt(k),px:v})})});
// 6. touch targets
document.querySelectorAll('a,button,summary').forEach(k=>{const r=R(k);if(!r.width)return;if(k.getAttribute('role')==='switch'){const row=k.parentElement;if(row&&R(row).height>=44)return;}if(k.tagName==='A'&&k.parentElement&&k.parentElement.tagName==='P'&&k.parentElement.textContent.trim().length>k.textContent.trim().length+3)return;if(r.height<44||r.width<44)out.push({regle:'cible tactile >= 44 px',element:name(k)+' '+txt(k),taille:Math.round(r.width)+'x'+Math.round(r.height)})});
// cascade: each child (.kid) icon starts at its parent's text start
document.querySelectorAll('.fam').forEach(fm=>{let parent=fm.querySelector('.fh > b');if(!parent){const d=fm.closest('details');parent=d&&d.querySelector('.tg > b');}if(!parent)return;const px=parent.getBoundingClientRect().left;
 fm.querySelectorAll('.kid > svg').forEach(s=>{if(!s.getBoundingClientRect().width)return;const d=s.getBoundingClientRect().left-px;if(Math.abs(d)>1)out.push({regle:'cascade : enfant sous le texte du parent',element:(s.parentElement.textContent||'').trim().slice(0,28),px:+d.toFixed(1)})})});
// cascade CFF: family icon under verdict text; child icon under family text
document.querySelectorAll('.s.info').forEach(c=>{const head=c.querySelector(':scope > div > div');if(!head)return;const key=head.getBoundingClientRect().left;
 c.querySelectorAll('.fh svg').forEach(s=>{const r=s.getBoundingClientRect();if(!r.width)return;const ring=c.querySelector(':scope > div > svg, :scope > div > span');const rr=ring.getBoundingClientRect();const d=r.right-rr.right;if(Math.abs(d)>1)out.push({regle:'icone de famille calee sur le bord droit de l anneau',px:+d.toFixed(1)});const tb=s.closest('.fh').querySelector('b');const dt=tb.getBoundingClientRect().left-key;if(Math.abs(dt)>1)out.push({regle:'texte de famille aligne sur le verdict',px:+dt.toFixed(1)})});
 c.querySelectorAll('.fam').forEach(fm=>{const t=fm.querySelector('.fh > b');if(!t)return;const tl=t.getBoundingClientRect().left;fm.querySelectorAll('.kd > svg').forEach(s=>{const r=s.getBoundingClientRect();if(!r.width)return;const d=r.left-tl;if(Math.abs(d)>1)out.push({regle:'cascade CFF : critere sous le texte de sa famille',element:(s.parentElement.textContent||'').trim().slice(0,24),px:+d.toFixed(1)})})});
 const pads=new Set([...c.querySelectorAll('.tg,.fh,.kd')].filter(e=>e.getBoundingClientRect().height).map(e=>getComputedStyle(e).paddingTop+'/'+getComputedStyle(e).paddingBottom));if(pads.size>1)out.push({regle:'espacement homogene des lignes',valeurs:[...pads]});
});
document.querySelectorAll('.s.info').forEach(c=>{const g=new Set();c.querySelectorAll('.fh,.kd').forEach(row=>{const sv=row.querySelector('svg');const t=row.querySelector('b, div');if(!sv||!t)return;const a=sv.getBoundingClientRect(),b=t.getBoundingClientRect();if(!a.width)return;g.add(Math.round(b.left-a.right))});if(g.size>1)out.push({regle:'meme ecart icone / texte partout',valeurs:[...g]})});
// dedupe
const seen=new Set();return out.filter(o=>{const k=JSON.stringify(o);if(seen.has(k))return false;seen.add(k);return true});
})()
