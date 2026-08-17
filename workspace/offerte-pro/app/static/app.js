
const rows=document.getElementById('rows');
function euro(n){return new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'}).format(n||0)}
function calc(){
  let sub=0,vat=0;
  document.querySelectorAll('.quote-row').forEach(r=>{
    const q=Number(r.querySelector('.qty').value||0);
    const p=Number(r.querySelector('.price').value||0);
    const v=Number(r.querySelector('.vat').value||0);
    sub+=q*p; vat+=q*p*(v/100);
  });
  subtotal.textContent=euro(sub); document.getElementById('vat').textContent=euro(vat); total.textContent=euro(sub+vat);
}
function addRow(){
  const r=document.createElement('div'); r.className='quote-row';
  r.innerHTML=`<input class="desc" placeholder="Omschrijving"><input class="qty" type="number" min="0" step="1" value="1"><input class="price" type="number" min="0" step=".01" placeholder="Prijs"><select class="vat"><option value="21">21%</option><option value="9">9%</option><option value="0">0%</option></select><button class="remove">×</button>`;
  r.querySelectorAll('input,select').forEach(x=>x.addEventListener('input',calc));
  r.querySelector('.remove').onclick=()=>{r.remove();calc()};
  rows.appendChild(r); calc();
}
addRow(); addRow();
document.getElementById('addRow').onclick=addRow;
document.getElementById('printBtn').onclick=()=>window.print();
document.getElementById('date').valueAsDate=new Date();
