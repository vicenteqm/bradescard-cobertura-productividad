const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.join(__dirname,'..'),elements={};
function el(id){return elements[id]??= {value:'',innerHTML:'',textContent:'',options:[],append(o){this.options.push(o)},classList:{toggle(){}},focus(){},setSelectionRange(){}}}
for(const id of ['region','socio','store','status','title','subtitle','scope','content','updated','export','reset'])el(id);
el('status').value='OPERANDO';
const context={window:{addEventListener(){}},document:{getElementById:el,createElement(){return {value:'',textContent:''}},querySelectorAll(){return []}},location:{hash:''},Intl,Date,Set,Blob,URL,setTimeout,console};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'site/data.js'),'utf8'),context);vm.runInContext(fs.readFileSync(path.join(root,'site/app.js'),'utf8'),context);
for(const s of ['cobertura','plantilla','tiendas','asistencia','productividad']){vm.runInContext(`section='${s}';render()`,context);assert(el('content').innerHTML.includes('table'),'Falta tabla en '+s);assert(!el('content').innerHTML.includes('NaN'),'NaN en '+s)}
for(const mode of ['tiendas','personas','nrt']){vm.runInContext(`section='productividad';prodMode='${mode}';render()`,context);assert(el('content').innerHTML.includes('table'))}
vm.runInContext("section='productividad';prodMode='personas';search='INEXISTENTE_xyz';render()",context);assert(el('content').innerHTML.includes('Sin registros'));
const m=vm.runInContext("metrics([{id:'A',estatus:'OPERANDO',promotores:1,sublideres:1,requerida:2}])[0]",context);assert.equal(m.conDatos,false);assert.equal(m.vacantes,null);
const actual=vm.runInContext('metrics(chosen())',context);for(const s of actual.filter(s=>s.conDatos)){assert.equal(s.cubiertas+s.vacantes,s.requerida);assert(s.cubiertas<=s.requerida)}
console.log('Interfaz: cinco vistas, tres modos de productividad, búsqueda vacía y reglas de cobertura verificadas.');
