"use strict";
const $=s=>document.querySelector(s), sayfa=document.body.dataset.sayfa;
const token=()=>sessionStorage.getItem('token');
const kullanici=()=>{try{return JSON.parse(sessionStorage.getItem('kullanici')||'null')}catch{return null}};
function bildirim(m,hata=false){const e=$('#bildirim');if(!e)return;e.textContent=m;e.className=hata?'uyari':'basari'}
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);if(cls)e.className=cls;return e}
function ekle(parent,tag,text,cls){const e=el(tag,text,cls);parent.append(e);return e}
function temiz(){const e=$('#icerik');if(e)e.replaceChildren();return e}
function girisGerekli(){if(!token()){bildirim('Bu işlem için giriş yapmalısınız.',true);return false}return true}
async function api(yol,method='GET',data){const h={'Accept':'application/json'};if(token())h.Authorization='Bearer '+token();if(data!==undefined)h['Content-Type']='application/json; charset=utf-8';let r;try{r=await fetch('/api'+yol,{method,headers:h,body:data===undefined?undefined:JSON.stringify(data)})}catch{throw Error('Sunucuya ulaşılamadı.')}const sonuc=await r.json().catch(()=>({}));if(!r.ok){if(r.status===401&&token()){sessionStorage.removeItem('token');sessionStorage.removeItem('kullanici');document.querySelectorAll('[data-yonetici]').forEach(e=>e.hidden=true);if($('#cikis'))$('#cikis').hidden=true}throw Error(sonuc.hata||sonuc.mesaj||'İstek başarısız (HTTP '+r.status+')')}return sonuc}
async function calistir(fn){try{await fn()}catch(e){bildirim(e.message,true)}}
function tarihAyarla(){if($('#tarih')){const d=new Date();$('#tarih').value=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}}
function tarihSaat(s){if(!s)return null;const d=new Date(String(s).replace(' ','T'));return Number.isNaN(d.getTime())?null:d}
function secenekleriDoldur(select,items){if(!select)return;const v=select.value;select.replaceChildren(new Option('Tümü',''));items.forEach(([id,ad])=>select.add(new Option(ad,String(id))));select.value=v}
let sonMenuler=[];
let seciliAlerjenler=[];
async function alerjenTercihleri(){
    seciliAlerjenler=[];
    if(!token())return;
    const d=await api('/profil/alerjenler');
    seciliAlerjenler=d.alerjenler.filter(a=>a.secili).map(a=>a.ad);
}
async function profilGetir(){
    if(!girisGerekli())return;
    const d=await api('/profil/alerjenler');
    const alan=$('#alerjenListesi');
    alan.replaceChildren();
    for(const a of d.alerjenler){
        const satir=ekle(alan,'p');
        const etiket=ekle(satir,'label');
        const kutu=ekle(etiket,'input');
        kutu.type='checkbox';
        kutu.value=a.id;
        kutu.checked=Boolean(a.secili);
        etiket.append(' '+a.ad);
    }
    $('#alerjenForm button').disabled=false;
}

function menuKart(m,rez=false){const c=el('article',undefined,'kart');ekle(c,'h2',`${m.yemekhane} · ${m.ogun}`);ekle(c,'p',m.tarih);const u=kullanici();const fiyat=u?.rol==='personel'?m.personel_fiyati:m.ogrenci_fiyati;ekle(c,'p',`${u?.rol==='personel'?'Personel fiyatınız':u?.rol==='ogrenci'?'Öğrenci fiyatınız':'Öğrenci fiyatı'}: ${fiyat} TL · Öğrenci: ${m.ogrenci_fiyati} TL · Personel: ${m.personel_fiyati} TL`);ekle(c,'p',`Toplam kalori: ${m.toplam_kalori} kcal`);const ul=ekle(c,'ul');(m.yemekler||[]).forEach(y=>{const li=ekle(ul,'li');ekle(li,'strong',y.ad);ekle(li,'span',` · ${y.kategori||'Yemek'} · ${y.kalori} kcal${y.vejetaryen?' · Vejetaryen':''}`);if(y.alerjenler){
    ekle(li,'span',' · Alerjenler: '+y.alerjenler,'alerjen');
    const eslesen=y.alerjenler.split(',').map(a=>a.trim()).filter(a=>seciliAlerjenler.includes(a));
    if(eslesen.length)ekle(li,'strong',' · ⚠ Alerjen uyarısı: '+eslesen.join(', '),'uyari');
}});ekle(c,'p',`Rezervasyon sonu: ${m.rezervasyon_son}`);
if(rez){
const porsiyon=el('select');
porsiyon.add(new Option('Tam porsiyon','tam'));
if([2,3].includes(Number(m.ogun_id)))porsiyon.add(new Option('Yarım porsiyon','yarim'));
const etiket=ekle(c,'label','Porsiyon: ');etiket.append(porsiyon);
const secilenFiyat=()=> (Number(fiyat)*(porsiyon.value==='yarim'?0.60:1)).toFixed(2);
const fiyatBilgi=ekle(c,'p','Seçilen fiyat: '+secilenFiyat()+' TL');
const dol=ekle(c,'p','Boş yer bilgisi yükleniyor...');const b=ekle(c,'button',`Rezervasyon Yap (${secilenFiyat()} TL)`,'dugme');b.disabled=true;const son=tarihSaat(m.rezervasyon_son);if(!son||son<=new Date()){b.disabled=true;b.textContent='Rezervasyon süresi doldu'}if(!token()){b.disabled=true;b.textContent='Rezervasyon için giriş yapın'}if(u?.rol==='yonetici'){b.disabled=true;b.textContent='Yönetici rezervasyon yapamaz'};
api(`/menuler/${m.menu_id}/doluluk`).then(d=>{dol.textContent=`Boş yer: ${d.bos_yer}/${d.kapasite} · Doluluk: %${d.doluluk_yuzde}`;if(d.bos_yer<=0){b.disabled=true;b.textContent='Kontenjan dolu'}else{const s=tarihSaat(d.rezervasyon_son);if(!s||s<=new Date()){b.disabled=true;b.textContent='Rezervasyon süresi doldu'}else if(token()&&u?.rol!=='yonetici'){b.disabled=false;b.textContent=`Rezervasyon Yap (${secilenFiyat()} TL)`}}}).catch(e=>{b.disabled=true;b.textContent='Rezervasyon şu anda kullanılamıyor';dol.textContent='Doluluk bilgisi alınamadı: '+e.message});
porsiyon.onchange=()=>{fiyatBilgi.textContent='Seçilen fiyat: '+secilenFiyat()+' TL';if(!b.disabled)b.textContent=`Rezervasyon Yap (${secilenFiyat()} TL)`};
b.onclick=()=>calistir(async()=>{if(!girisGerekli()||b.disabled)return;b.disabled=true;try{const d=await api('/rezervasyon/yap','POST',{menu_id:m.menu_id,porsiyon:porsiyon.value});bildirim(`Rezervasyon başarılı. Numara: ${d.rezervasyon.rezervasyon_id}. Kalan bakiye: ${d.rezervasyon.bakiye} TL`);b.textContent='Rezervasyon yapıldı';porsiyon.disabled=true}catch(e){b.disabled=false;throw e}})}return c}
function filtrele(){const alan=temiz();const y=$('#yemekhaneFiltre')?.value||'',o=$('#ogunFiltre')?.value||'';const liste=sonMenuler.filter(m=>(!y||String(m.yemekhane_id)===y)&&(!o||String(m.ogun_id)===o));if(!liste.length)ekle(alan,'p','Bu filtrelerde menü bulunamadı.');liste.forEach(m=>alan.append(menuKart(m,sayfa==='haftalik')));bildirim(`${liste.length} menü listelendi.`)}
async function menuler(haftalik){await alerjenTercihleri();const t=$('#tarih').value;if(!t)throw Error('Tarih seçiniz.');const d=await api(`/menuler/${haftalik?'haftalik':'gunluk'}?tarih=${encodeURIComponent(t)}`);sonMenuler=d.menuler||[];const unique=(key,label)=>[...new Map(sonMenuler.map(m=>[m[key],[m[key],m[label]]])).values()];secenekleriDoldur($('#yemekhaneFiltre'),unique('yemekhane_id','yemekhane'));secenekleriDoldur($('#ogunFiltre'),unique('ogun_id','ogun'));filtrele()}
async function rezervasyonlari(){
 if(!girisGerekli())return;
 const d=await api('/rezervasyonlar');const alan=temiz();
 if(!d.rezervasyonlar?.length){ekle(alan,'p','Rezervasyonunuz yok.');return}
 const gunIstekleri=new Map();
 for(const r of d.rezervasyonlar){
  const c=ekle(alan,'article',undefined,'kart');
  ekle(c,'h2',`${r.yemekhane} · ${r.ogun}`);
  ekle(c,'p',`${r.tarih} · ${r.ucret} TL · ${r.porsiyon==='yarim'?'Yarım':'Tam'} porsiyon · Durum: ${r.durum}`);
  ekle(c,'p',`Rezervasyon #${r.id} · Menü #${r.menu_id}`);
  if(r.durum!=='aktif')continue;
  const b=ekle(c,'button','İptal koşulları kontrol ediliyor...','dugme');b.disabled=true;
  const bilgi=ekle(c,'p','Rezervasyon son saati sorgulanıyor.');
  try{
   // Her tarih için menüleri tek sefer getir; iptal son saati sunucudan öğren.
   const gun=String(r.tarih).slice(0,10);
   if(!gunIstekleri.has(gun))gunIstekleri.set(gun,api('/menuler/gunluk?tarih='+encodeURIComponent(gun)));
   const gunluk=await gunIstekleri.get(gun);
   const menu=(gunluk.menuler||[]).find(m=>Number(m.menu_id)===Number(r.menu_id));
   if(!menu)throw Error('Menüye ait iptal son saati doğrulanamadı.');
   const son=tarihSaat(menu.rezervasyon_son);
   if(!son)throw Error('Rezervasyon son saati okunamadı.');
   bilgi.textContent='Son iptal saati: '+menu.rezervasyon_son;
   if(new Date()>=son){b.textContent='İptal süresi doldu';continue}
   b.disabled=false;b.textContent='Rezervasyonu İptal Et';
   b.onclick=()=>calistir(async()=>{
    if(new Date()>=son){b.disabled=true;throw Error('Rezervasyon iptal süresi doldu.')}
    if(!confirm('Rezervasyonu iptal etmek istiyor musunuz?'))return;
    b.disabled=true;
    try{await api('/rezervasyon/iptal','POST',{rezervasyon_id:r.id});await rezervasyonlari();bildirim('Rezervasyon iptal edildi.')}
    catch(e){b.disabled=false;throw e}
   });
  }catch(e){b.textContent='İptal şu anda kullanılamıyor';bilgi.textContent=e.message}
 }
}
async function bakiyeGetir(){if(!girisGerekli())return;const d=await api('/bakiye');$('#bakiyeBilgi').replaceChildren(el('h2',`Güncel bakiye: ${d.bakiye} TL`));const alan=temiz();const wrap=ekle(alan,'div',undefined,'tablo-kaydir'),tab=ekle(wrap,'table'),thead=ekle(tab,'thead'),tr=ekle(thead,'tr');['Tarih','İşlem','Tutar','Açıklama'].forEach(t=>ekle(tr,'th',t));const tbody=ekle(tab,'tbody');d.hareketler.forEach(h=>{const r=ekle(tbody,'tr');[h.olusturma,h.tur,h.tutar+' TL',h.aciklama||''].forEach(t=>ekle(r,'td',t))})}
function formVeri(form){return Object.fromEntries(new FormData(form).entries())}
function adminVeri(form,duzenle=false){const d=formVeri(form);const ids=d.yemek_idleri.split(',').map(s=>Number(s.trim()));if(!ids.length||ids.some(i=>!Number.isInteger(i)||i<=0))throw Error('Yemek numaralarını virgülle ve doğru giriniz.');const x={ogrenci_fiyati:Number(d.ogrenci_fiyati),personel_fiyati:Number(d.personel_fiyati),yemek_idleri:ids};if(duzenle)x.menu_id=Number(d.menu_id);else Object.assign(x,{yemekhane_id:Number(d.yemekhane_id),ogun_id:Number(d.ogun_id),tarih:d.tarih});return x}
async function yoneticiGetir(){if(!girisGerekli())return;if(kullanici()?.rol!=='yonetici'){bildirim('Bu sayfa yalnızca yöneticilere açıktır.',true);return}const d=await api('/yonetici/menuler');const alan=temiz(),wrap=ekle(alan,'div',undefined,'tablo-kaydir'),tab=ekle(wrap,'table'),head=ekle(ekle(tab,'thead'),'tr');['ID','Tarih','Yemekhane','Öğün','Öğrenci TL','Personel TL','Boş/Kapasite','Doluluk %','Ortalama puan'].forEach(t=>ekle(head,'th',t));const body=ekle(tab,'tbody');d.menuler.forEach(m=>{const tr=ekle(body,'tr');[m.menu_id,m.tarih,m.yemekhane,m.ogun,m.ogrenci_fiyati,m.personel_fiyati,`${m.bos_yer}/${m.kapasite}`,m.doluluk_yuzde,m.ortalama_puan===null?'Henüz yok':`${m.ortalama_puan} (${m.oy_sayisi} oy)`].forEach(v=>ekle(tr,'td',v))});bildirim(`${d.menuler.length} menü görüntülendi.`)}
async function degerlendirmeleriGetir(){if(!girisGerekli())return;const d=await api('/rezervasyonlar');const liste=d.rezervasyonlar.filter(r=>r.durum==='kullanildi');const select=$('#degerMenu');select.replaceChildren(new Option('Menü seçiniz',''));const ids=new Set();const alan=temiz();liste.forEach(r=>{if(ids.has(r.menu_id))return;ids.add(r.menu_id);select.add(new Option(`${r.tarih} · ${r.yemekhane} · ${r.ogun} (#${r.menu_id})`,r.menu_id));ekle(alan,'p',`${r.tarih} · ${r.yemekhane} · ${r.ogun}`)});if(!liste.length){ekle(alan,'p','Henüz kullanılmış rezervasyonunuz yok.');$('#puanForm').querySelector('button').disabled=true}}
$('#cikis').onclick=()=>calistir(async()=>{try{await api('/cikis','POST')}finally{sessionStorage.removeItem('token');sessionStorage.removeItem('kullanici');location.href='/index.html'}});
if(token()){$('#cikis').hidden=false;$('#oturumBilgi').textContent=`${kullanici()?.ad||'Kullanıcı'} · ${kullanici()?.rol||''}`}
document.querySelectorAll('[data-yonetici]').forEach(e=>e.hidden=kullanici()?.rol!=='yonetici');if(sayfa==='yonetici'&&kullanici()?.rol!=='yonetici'){document.querySelectorAll('#ekleForm,#duzenleForm,[data-admin-form]').forEach(e=>e.hidden=true)}
tarihAyarla();
if(sayfa==='giris'){$('#girisForm').onsubmit=e=>{e.preventDefault();calistir(async()=>{const d=await api('/giris','POST',formVeri(e.target));sessionStorage.setItem('token',d.token);sessionStorage.setItem('kullanici',JSON.stringify(d.kullanici));location.href='/gunluk-menu.html'})};if(token())$('#profil').textContent='Oturumunuz açık. Menü sayfasına geçebilirsiniz.'}
if(sayfa==='gunluk'||sayfa==='haftalik'){$('#yemekhaneFiltre').onchange=filtrele;$('#ogunFiltre').onchange=filtrele;const haftalik=sayfa==='haftalik';$(haftalik?'#haftalikGetir':'#gunlukGetir').onclick=()=>calistir(()=>menuler(haftalik));calistir(()=>menuler(haftalik))}
if(sayfa==='rezervasyonlar'){$('#rezGetir').onclick=()=>calistir(rezervasyonlari);calistir(rezervasyonlari)}
if(sayfa==='bakiye'){$('#bakiyeForm').onsubmit=e=>{e.preventDefault();calistir(async()=>{const tutar=Number(new FormData(e.target).get('tutar'));if(!Number.isFinite(tutar)||tutar<=0)throw Error('Geçerli bir tutar giriniz.');await api('/bakiye/yukle','POST',{tutar});e.target.reset();await bakiyeGetir();bildirim('Bakiye yüklendi.')})};calistir(bakiyeGetir)}
if(sayfa==='degerlendirme'){$('#puanForm').onsubmit=e=>{e.preventDefault();calistir(async()=>{const d=formVeri(e.target);await api('/degerlendirme/ekle','POST',{menu_id:Number(d.menu_id),puan:Number(d.puan),yorum:d.yorum});e.target.reset();await degerlendirmeleriGetir();bildirim('Değerlendirme kaydedildi.')})};calistir(degerlendirmeleriGetir)}
if(sayfa==='yonetici'){$('#ekleForm').onsubmit=e=>{e.preventDefault();calistir(async()=>{const d=await api('/yonetici/menu/ekle','POST',adminVeri(e.target));e.target.reset();await yoneticiGetir();bildirim(`Menü eklendi. ID: ${d.menu_id}`)})};$('#duzenleForm').onsubmit=e=>{e.preventDefault();calistir(async()=>{await api('/yonetici/menu/duzenle','PUT',adminVeri(e.target,true));await yoneticiGetir();bildirim('Menü güncellendi.')})};calistir(yoneticiGetir)}

if(!document.querySelector('nav a[href="/profil.html"]')){
    const nav=document.querySelector('nav');
    if(nav){const a=el('a','Profilim');a.href='/profil.html';nav.insertBefore(a,nav.querySelector('[data-yonetici]'));}
}
if(sayfa==='profil'){
    $('#alerjenForm').onsubmit=e=>{
        e.preventDefault();
        calistir(async()=>{
            const alerjenler=[...document.querySelectorAll('#alerjenListesi input:checked')].map(k=>Number(k.value));
            await api('/profil/alerjenler','PUT',{alerjenler});
            bildirim('Alerjen tercihleriniz kaydedildi.');
        });
    };
    calistir(profilGetir);
}
