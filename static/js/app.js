var TRANSLATIONS=window.TRANSLATIONS||{};
function t(key,opts){var s=TRANSLATIONS[key]!==undefined?TRANSLATIONS[key]:key;if(opts){for(var k in opts)s=String(s).replace(new RegExp('\\{'+k+'\\}','g'),opts[k]);}return s;}
let stream=null,isScanning=false,lastScannedCode=null,currentFacingMode='environment';
function isIOS(){return/iPhone|iPad|iPod/i.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);}
function getVideoConstraints(){return isIOS()?{video:{facingMode:{ideal:currentFacingMode},width:{min:320},height:{min:240}},audio:false}:{video:{facingMode:currentFacingMode,width:{ideal:1280},height:{ideal:720}},audio:false};}

(function sidebarToggle(){
  var btn=document.getElementById('sidebarToggle'),sidebar=document.getElementById('sidebar'),overlay=document.getElementById('sidebarOverlay');
  function toggle(){var open=sidebar.classList.toggle('open');btn.classList.toggle('sidebar-open',open);if(overlay)overlay.classList.toggle('visible',open);}
  if(btn&&sidebar){btn.addEventListener('click',toggle);if(overlay)overlay.addEventListener('click',function(){sidebar.classList.remove('open');btn.classList.remove('sidebar-open');overlay.classList.remove('visible');});}
})();

var productForm=document.getElementById('productForm');
if(productForm){
  productForm.addEventListener('submit',async function(e){
    e.preventDefault();
    const name=document.getElementById('productName').value.trim(),price=parseFloat(document.getElementById('productPrice').value);
    if(!name||isNaN(price)||price<=0){alert(t('enter_valid_name_price'));return;}
    try{
      const r=await fetch('/api/products',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,price})});
      if(r.ok)window.location.href='/products';else{const d=await r.json();alert(d.error||t('failed'));}
    }catch(err){alert(t('failed'));}
    this.reset();
  });
}

async function addToCartFromList(productId){
  try{
    const r=await fetch('/api/cart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:productId})});
    if(r.ok)location.reload();else alert(t('failed'));
  }catch(e){alert(t('failed'));}
}

async function clearCart(){
  if(!confirm(t('clear_cart_confirm')))return;
  try{
    const r=await fetch('/api/cart',{method:'DELETE'});
    if(r.ok)location.reload();else alert(t('failed'));
  }catch(e){alert(t('failed'));}
}

async function finishBuy(){
  try{
    const r=await fetch('/api/cart/checkout',{method:'POST',headers:{'Content-Type':'application/json'}});
    const d=await r.json();
    if(r.ok){alert(d.message||t('checkout_success'));window.location.href='/products-sold';}
    else alert(d.error||t('failed'));
  }catch(e){alert(t('failed'));}
}

function openEditModal(id,name,price){
  var m=document.getElementById('editProductModal'),f=document.getElementById('editProductForm');
  if(m&&f){document.getElementById('editProductId').value=id;document.getElementById('editProductName').value=name;document.getElementById('editProductPrice').value=price;m.classList.add('active');}
}
function closeEditModal(){
  var m=document.getElementById('editProductModal'),f=document.getElementById('editProductForm');
  if(m){m.classList.remove('active');}if(f){f.reset();}
}
var editProductForm=document.getElementById('editProductForm');
if(editProductForm){
  editProductForm.addEventListener('submit',async function(e){
    e.preventDefault();
    const id=document.getElementById('editProductId').value,name=document.getElementById('editProductName').value.trim(),price=parseFloat(document.getElementById('editProductPrice').value);
    if(!name||isNaN(price)||price<=0){alert(t('invalid'));return;}
    try{
      const r=await fetch('/api/products/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,price})});
      if(r.ok){closeEditModal();location.reload();}else{alert((await r.json()).error||t('failed'));}
    }catch(e){alert(t('failed'));}
  });
}

async function deleteProduct(productId,productName){
  if(!confirm(t('delete_product_confirm',{name:productName})))return;
  try{
    const r=await fetch('/api/products/'+productId,{method:'DELETE'});
    if(r.ok)location.reload();else alert((await r.json()).error||t('failed'));
  }catch(e){alert(t('failed'));}
}

function filterProductList(){
  const q=((document.getElementById('productSearch')||{}).value||'').trim().toLowerCase();
  const noResultsEl=document.getElementById('productsNoResults');
  const rows=document.querySelectorAll('#productsList .product-row');
  let visible=0;
  rows.forEach(row=>{
    const name=(row.querySelector('.product-name')||{}).textContent||'';
    const match=!q||name.toLowerCase().includes(q);
    row.style.display=match?'':'none';
    if(match)visible++;
  });
  if(noResultsEl)noResultsEl.style.display=visible===0&&rows.length>0?'block':'none';
  const sel=document.getElementById('selectAllProducts');
  if(sel){ const visibleInputs=Array.from(rows).filter(r=>r.style.display!=='none').map(r=>r.querySelector('.product-checkbox-input')).filter(Boolean); sel.checked=visibleInputs.length>0&&visibleInputs.every(cb=>cb.checked); }
  updateBulkDeleteButton();
}
function toggleSelectAll(){
  var sel=document.getElementById('selectAllProducts');
  if(!sel)return;
  const all=sel.checked;
  document.querySelectorAll('#productsList .product-row').forEach(row=>{
    if(row.style.display==='none')return;
    const cb=row.querySelector('.product-checkbox-input');
    if(cb)cb.checked=all;
  });
  updateBulkDeleteButton();
}
function updateBulkDeleteButton(){
  const n=document.querySelectorAll('.product-checkbox-input:checked').length;
  const b1=document.getElementById('bulkDeleteBtn'),b2=document.getElementById('bulkPrintBtn'),b3=document.getElementById('bulkAddToCartBtn');
  if(b1)b1.style.display=n?'block':'none';
  if(b2)b2.style.display=n?'block':'none';
  if(b3)b3.style.display=n?'block':'none';
}

async function addSelectedToCart(){
  const ids=Array.from(document.querySelectorAll('.product-checkbox-input:checked')).map(c=>c.value);
  if(!ids.length){alert(t('select_at_least_one'));return;}
  try{
    for(const productId of ids){
      const r=await fetch('/api/cart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:productId})});
      if(!r.ok){alert((await r.json()).error||t('failed'));return;}
    }
    alert(t('msg_added_n_to_cart',{n:ids.length}));
    location.reload();
  }catch(e){alert(t('failed'));}
}

async function bulkDeleteProducts(){
  const ids=Array.from(document.querySelectorAll('.product-checkbox-input:checked')).map(c=>c.value);
  if(!ids.length){alert(t('select_at_least_one'));return;}
  if(!confirm(t('delete_products_confirm',{n:ids.length})))return;
  try{
    const r=await fetch('/api/products/bulk-delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_ids:ids})});
    if(r.ok){const d=await r.json();alert(d.message);location.reload();}else alert((await r.json()).error||t('failed'));
  }catch(e){alert(t('failed'));}
}

async function preparePrintFromCart(){
  try{
    const r=await fetch('/api/cart'),d=await r.json(),cart=d.cart||[];
    if(!cart.length){alert(t('cart_empty'));return;}
    const items=cart.map(item=>{
      let pid=item.product_id;
      if(!pid){
        document.querySelectorAll('.product-row').forEach(row=>{
          if(row.querySelector('.product-name').textContent.trim()===item.name)
            pid=row.getAttribute('data-product-id');
        });
      }
      return{name:item.name,price:item.price,qrUrl:pid?'/api/products/'+pid+'/qr':null};
    });
    openPrintModal(items,t('carrinho'));
  }catch(e){alert(t('failed'));}
}

async function preparePrintFromProducts(){
  const checkboxes=document.querySelectorAll('.product-checkbox-input:checked');
  if(!checkboxes.length){alert(t('select_at_least_one'));return;}
  const items=Array.from(checkboxes).map(cb=>{
    const row=cb.closest('.product-row'),name=row.querySelector('.product-name').textContent.trim(),priceText=row.querySelector('.product-price').textContent.trim(),price=parseFloat(priceText.replace(/[R$\s$]/g,'').replace(',','.'))||0;
    return{name,price,qrUrl:'/api/products/'+cb.value+'/qr'};
  });
  openPrintModal(items,t('produtos_selecionados'));
}

function openPrintModal(items,title){
  const html=['<div class="print-title"><h1>'+title+'</h1><p class="print-date">'+new Date().toLocaleString()+'</p></div><div class="print-items-grid">'];
  items.forEach(item=>{
    const qr=item.qrUrl?'<img src="'+item.qrUrl+'" alt="QR" class="print-qr-image">':'<p class="no-qr">'+t('no_qr')+'</p>';
    var cur=TRANSLATIONS.currency||'$';
    html.push('<div class="print-item"><div class="print-item-header"><h3 class="print-item-name">'+escapeHtml(item.name)+'</h3><div class="print-item-price">'+cur+' '+item.price.toFixed(2).replace('.',',')+'</div></div><div class="print-item-qr">'+qr+'</div></div>');
  });
  const total=items.reduce((s,i)=>s+i.price,0);
  var cur=TRANSLATIONS.currency||'$';
  html.push('</div><div class="print-footer"><p>'+t('items')+': '+items.length+'</p><p>'+t('total')+': '+cur+' '+total.toFixed(2).replace('.',',')+'</p></div>');
  document.getElementById('printContent').innerHTML=html.join('');
  document.getElementById('printModal').classList.add('active');
}
function closePrintModal(){document.getElementById('printModal').classList.remove('active');}
function escapeHtml(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML;}

var editProductModal=document.getElementById('editProductModal');
if(editProductModal)editProductModal.addEventListener('click',e=>{if(e.target.id==='editProductModal')closeEditModal();});
var printModal=document.getElementById('printModal');
if(printModal)printModal.addEventListener('click',e=>{if(e.target.id==='printModal')closePrintModal();});

function openScanner(){
  if(!document.getElementById('scannerModal'))return;
  if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){alert(t('camera_not_supported'));return;}
  document.getElementById('scannerModal').classList.add('active');
  document.body.style.overflow='hidden';
  isScanning=false;lastScannedCode=null;currentFacingMode='environment';
  const v=document.getElementById('video');v.setAttribute('playsinline',true);v.setAttribute('webkit-playsinline',true);v.muted=true;
  startCamera();
}
function startCamera(){
  const video=document.getElementById('video'),status=document.getElementById('scannerStatus'),switchBtn=document.getElementById('switchCameraBtn');
  status.textContent=t('requesting_camera');
  navigator.mediaDevices.getUserMedia(getVideoConstraints()).then(mediaStream=>{
    stream=mediaStream;video.srcObject=stream;
    video.onloadedmetadata=()=>{
      video.play().then(()=>{status.textContent=t('point_at_qr');isScanning=true;startScanning();}).catch(()=>{status.textContent=t('error_starting_camera');status.className='scanner-status error';});
    };
  }).catch(err=>{
    isScanning=false;
    let msg=t('camera_denied');
    if(err.name==='NotAllowedError')msg+=t('allow_in_settings');
    else if(err.name==='NotFoundError')msg+=t('no_camera_found');
    else if(err.name==='OverconstrainedError'&&isIOS()){status.textContent=t('trying');navigator.mediaDevices.getUserMedia({video:true}).then(s=>{stream=s;video.srcObject=s;video.onloadedmetadata=()=>{video.play().then(()=>{isScanning=true;startScanning();});};}).catch(()=>{status.textContent=t('camera_error');});return;}
    else msg+=err.message||'';
    status.textContent=msg;status.className='scanner-status error';
  });
}
function startScanning(){
  const video=document.getElementById('video'),canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d');
  function scan(){
    if(!isScanning||!video||video.readyState!==4)return;
    const w=video.videoWidth,h=video.videoHeight;
    if(w>0&&h>0){canvas.width=w;canvas.height=h;ctx.drawImage(video,0,0,w,h);
      const id=ctx.getImageData(0,0,w,h),code=jsQR(id.data,id.width,id.height);
      if(code&&code.data!==lastScannedCode){lastScannedCode=code.data;handleScannedQR(code.data);}
    }
    requestAnimationFrame(scan);
  }
  scan();
}
function switchCamera(){
  if(!stream)return;
  stream.getTracks().forEach(t=>t.stop());
  currentFacingMode=currentFacingMode==='environment'?'user':'environment';
  startCamera();
}
function closeScanner(){
  document.getElementById('scannerModal').classList.remove('active');
  document.body.style.overflow='';
  isScanning=false;lastScannedCode=null;
  if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
  const v=document.getElementById('video'),s=document.getElementById('scannerStatus');
  if(v)v.srcObject=null;
  if(s){s.textContent=t('point_at_qr');s.className='scanner-status';}
}
async function handleScannedQR(data){
  if(!isScanning)return;
  isScanning=false;
  document.getElementById('scannerStatus').textContent=t('processing');
  try{
    const obj=JSON.parse(data);
    const r=await fetch('/api/cart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});
    var cur=TRANSLATIONS.currency||'$';
    if(r.ok){document.getElementById('scannerStatus').textContent=t('added')+': '+obj.name+' - '+cur+' '+obj.price.toFixed(2).replace('.',',');setTimeout(()=>{closeScanner();location.reload();},1000);}
    else{document.getElementById('scannerStatus').textContent=t('failed');document.getElementById('scannerStatus').className='scanner-status error';setTimeout(()=>{isScanning=true;document.getElementById('scannerStatus').textContent=t('point_at_qr');},2000);}
  }catch(e){document.getElementById('scannerStatus').textContent=t('invalid_qr');document.getElementById('scannerStatus').className='scanner-status error';setTimeout(()=>{isScanning=true;document.getElementById('scannerStatus').textContent=t('point_at_qr');},2000);}
}
var scannerModal=document.getElementById('scannerModal');
if(scannerModal)scannerModal.addEventListener('click',e=>{if(e.target.id==='scannerModal')closeScanner();});
