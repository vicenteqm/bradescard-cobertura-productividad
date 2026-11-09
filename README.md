# Bradescard · Control de cobertura y productividad

Tablero independiente con Cobertura, Plantilla, Tiendas, Asistencia y Productividad. Abre `site/index.html` o ejecuta `ACTUALIZAR_BRADESCARD.bat` para actualizar y abrir. No necesita servidor ni compilación.

## Actualizar

1. Instala Python 3.10+ y `pip install -r requirements.txt`.
2. Copia `config.example.json` a `config.local.json`. Coloca los cinco archivos en `inputs/` y ajusta las rutas y el corte de asistencia.
3. Ejecuta `python actualizar.py`. Se valida todo antes de reemplazar `site/data.js`. Un error conserva la versión anterior.
4. Abre el tablero. Los filtros de región, socio, tienda y estatus aplican a todas las pestañas. Descargar CSV exporta la tabla visible con sus filtros.

Los originales, dependencias y configuración local quedan excluidos de Git. Los datos del tablero contienen nombres y horarios solicitados; no incluyen nóminas, teléfonos, correos, credenciales ni remuneraciones. El repositorio se prepara privado. No hay descarga automática de fuentes ni publicación programada.

## Cobertura y plantilla

- Universo de cobertura: tiendas OPERANDO. El catálogo conserva también los demás estatus.
- Clave de tienda: socio + determinante, con normalización de mayúsculas y ceros iniciales.
- Requeridos: promotores + sublíderes; se comprueba contra plantilla autorizada.
- Activos: ACTIVO en perfiles PROMOTOR DE CREDITO y SUBLIDER. Otros puestos se muestran en Plantilla.
- Cubiertas: suma por tienda y perfil de `min(activos, requeridos)`. Vacantes: suma de `max(requeridos - activos, 0)`. Los excedentes no compensan otros perfiles o tiendas.
- Si no existen personas de los perfiles elegibles para una tienda, queda sin datos y sus plazas se excluyen del denominador de cobertura. Se informa el total pendiente.
- Identidad interna: nómina + nombre normalizado. Se excluyen los identificadores del tablero. La última semana de aparición determina el estatus; no aparecer en una semana no implica baja.
- Las semanas se ordenan por fecha de finalización. Fechas de las columnas se reconstruyen y validan con sus días; se excluyen otros meses y fechas posteriores al corte explícito. Gana la semana más reciente en solapamientos. Vacío significa SIN CAPTURA, no falta.
- Los horarios se copian de la fuente. No se inventan turnos de plazas vacantes ni se confunden con checadas.

## Productividad

**Por tienda** cruza BI y TXH con la base. Incluye región, ciudad, estado, socio, tienda, nombre de tienda, grupo, ticket, conversión, TXH, trámites, aprobadas, tasa de aprobación, activadas, meta y alcance al día, meta y alcance mensual, AMD y % AMD.

**Por persona** usa Staff BETTER: nombre, puesto, TXH, trámites correctos, aprobadas, aprobadas/correctos, activadas y % AMD. Ticket, metas y conversión solo existen por tienda; no se distribuyen arbitrariamente entre personas.

**NRT** conserva el corte parcial independiente. No se suma al mensual ni se considera embosadas equivalente a activadas.

Las fechas se leen de los reportes. BI y TXH deben tener el mismo periodo de trámites. Trámites y activaciones tienen cortes distintos, visibles en pantalla. El grupo proviene de la base autorizada.

Conversión = trámites totales / ticket estimado. Metas corresponden a activaciones. Alcance diario = activadas / meta al día; alcance mensual = activadas / meta mensual. Las tasas por fila se conservan del BI. Las tarjetas aprobadas total incluyen PP, pero la tasa BI es exclusivamente PLCC + VISA, como indica su encabezado. AMD significa activación el mismo día; cantidad y porcentaje PLCC + VISA se muestran por separado.

TXH se conserva del reporte. No se promedian tasas ni se reconstruyen horas a partir de TXH redondeado. División sin denominador válido se muestra como no disponible. Las tiendas BI fuera de la base se excluyen y se informa su cantidad.

## Verificación

`python -m unittest discover -s tests -v` comprueba claves, cobertura de fuentes, tasas y conciliación de totales. `node tests/interfaz.cjs` verifica la ejecución de las cinco vistas y las reglas de cobertura. La revisión visual en navegador está pendiente: el navegador de esta sesión bloqueó el acceso al archivo local.
