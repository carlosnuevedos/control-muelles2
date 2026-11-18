function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  
  try {
    var data = JSON.parse(e.postData.contents);
    var action = data.action;

    // --- LECTURA: CONTROL DE LANZADERAS ---
    if (action === "leer") {
      var sheet = ss.getSheetByName("Control Lanzaderas");
      var rows = sheet.getDataRange().getValues();
      return ContentService.createTextOutput(JSON.stringify({rows: rows}))
                           .setMimeType(ContentService.MimeType.JSON);
    }
    
    // --- LECTURA: CARGAS DE CLIENTE ---
    if (action === "leer_clientes") {
      var sheet = ss.getSheetByName("Cargas de cliente");
      var rows = sheet.getDataRange().getValues();
      return ContentService.createTextOutput(JSON.stringify({rows: rows}))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    // --- LECTURA: PRODUCCIÓN ---
    if (action === "leer_produccion") {
      var sheet = ss.getSheetByName("Producción");
      var rows = sheet.getDataRange().getValues();
      return ContentService.createTextOutput(JSON.stringify({rows: rows}))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    // --- LECTURA: REUB, COMP Y NCT'S ---
    if (action === "leer_reub") {
      var sheet = ss.getSheetByName("Reub, Comp y NCT's");
      var rows = sheet.getDataRange().getValues();
      return ContentService.createTextOutput(JSON.stringify({rows: rows}))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    // --- ESCRITURA: CONTROL DE LANZADERAS ---
    // A: Fecha Registro | B: Mes | C: Matrícula | D: Albarán | E: Operación | F: Hora Llegada | G: Hora Inicio | H: Hora Fin
    // I: Min. Espera | J: Min. Operación | K: Min. Totales | L: Pallets | M: Carretillero | N: Turno | O: Incidencias | P: Semana | Q: Día
    if (action === "update") {
      var sheet = ss.getSheetByName("Control Lanzaderas");
      var rowsToAdd = data.rows;
      
      for (var i = 0; i < rowsToAdd.length; i++) {
        var row = rowsToAdd[i];
        var fechaParts = row[0].split("-");
        var d = new Date(fechaParts[0], fechaParts[1] - 1, fechaParts[2]);
        var semanaISO = getISOWeek(d);
        var diaSemana = getDiaSemanaEspanol(d);
        
        var filaFinal = [
          row[0],    // A: Fecha Registro
          "",        // B: Mes (Fórmula ARRAYFORMULA en B5)
          row[1],    // C: Matrícula
          row[2],    // D: Albarán
          row[3],    // E: Operación
          row[4],    // F: Hora Llegada
          row[5],    // G: Hora Inicio
          row[6],    // H: Hora Fin
          row[7],    // I: Min. Espera
          row[8],    // J: Min. Operación
          row[9],    // K: Min. Totales
          row[10],   // L: Pallets
          row[11],   // M: Carretillero
          row[12],   // N: Turno
          row[13],   // O: Incidencias
          semanaISO, // P: Semana
          diaSemana  // Q: Día
        ];
        
        sheet.appendRow(filaFinal);
      }
      
      return ContentService.createTextOutput(JSON.stringify({status: "success"}))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    // --- ESCRITURA: CARGAS DE CLIENTE ---
    // A: Fecha Registro | B: Mes | C: Nº Transporte | D: H. Picada | E: H. Comienzo | F: Hora Fin | G: Min. Operación
    // H: Min. Espera totales | I: Pallets | J: Carretillero | K: ¿Etiquetas? | L: Turno | M: Incidencia | N: Semana | O: Día
    if (action === "update_cliente") {
      var sheet = ss.getSheetByName("Cargas de cliente");
      var rowsToAdd = data.rows;
      
      for (var i = 0; i < rowsToAdd.length; i++) {
        var row = rowsToAdd[i];
        var fechaParts = row[0].split("-");
        var d = new Date(fechaParts[0], fechaParts[1] - 1, fechaParts[2]);
        var semanaISO = getISOWeek(d);
        var diaSemana = getDiaSemanaEspanol(d);
        
        var filaFinal = [
          row[0],    // A: Fecha Registro
          "",        // B: Mes (Fórmula ARRAYFORMULA en B5)
          row[1],    // C: Nº Transporte
          row[2],    // D: H. Picada
          row[3],    // E: H. Comienzo
          row[4],    // F: Hora Fin
          row[5],    // G: Min. Operación
          row[6],    // H: Min. Espera totales
          row[7],    // I: Pallets
          row[8],    // J: Carretillero
          row[9],    // K: ¿Etiquetas?
          row[10],   // L: Turno
          row[11],   // M: Incidencia
          semanaISO, // N: Semana
          diaSemana  // O: Día
        ];
        
        sheet.appendRow(filaFinal);
      }
      
      return ContentService.createTextOutput(JSON.stringify({status: "success"}))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    // --- ESCRITURA: PRODUCCIÓN ---
    // A: Fecha Registro | B: Mes | C: Día | D: Semana | E: Carretillero | F: Pallets Maquilado | G: Pallets Chequeo | H: Tiempo Maquilado | I: Tiempo Chequeo | J: Turno
    if (action === "update_produccion") {
      var sheet = ss.getSheetByName("Producción");
      var rowsToAdd = data.rows;
      
      for (var i = 0; i < rowsToAdd.length; i++) {
        var row = rowsToAdd[i];
        var fechaParts = row[0].split("-");
        var d = new Date(fechaParts[0], fechaParts[1] - 1, fechaParts[2]);
        var semanaISO = getISOWeek(d);
        var diaSemana = getDiaSemanaEspanol(d);
        
        var filaFinal = [
          row[0],    // A: Fecha Registro
          "",        // B: Mes (Fórmula ARRAYFORMULA en B5)
          diaSemana, // C: Día
          semanaISO, // D: Semana
          row[1],    // E: Carretillero
          row[2],    // F: Pallets Maquilado
          row[3],    // G: Pallets Chequeo
          row[4],    // H: Tiempo Maquilado
          row[5],    // I: Tiempo Chequeo
          row[6]     // J: Turno
        ];
        
        sheet.appendRow(filaFinal);
      }
      
      return ContentService.createTextOutput(JSON.stringify({status: "success"}))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    // --- ESCRITURA: REUB, COMP Y NCT'S ---
    // A: Fecha Registro | B: Mes | C: Turno | D: Semana | E: Día | F: Carretillero R. | G: Nº Pallets Reub.
    // H: Carretillero C. | I: Nº Compact. | J: Tiempo Compact | K: Carretillero NCT | L: Nº Pedido | M: Nº Cajas | N: Tiempo NCT
    if (action === "update_reub") {
      var sheet = ss.getSheetByName("Reub, Comp y NCT's");
      var rowsToAdd = data.rows;
      
      for (var i = 0; i < rowsToAdd.length; i++) {
        var row = rowsToAdd[i];
        var fechaStr = row[0];
        var turno = row[1];
        
        var fechaParts = fechaStr.split("-");
        var d = new Date(fechaParts[0], fechaParts[1] - 1, fechaParts[2]);
        var semanaISO = getISOWeek(d);
        var diaSemana = getDiaSemanaEspanol(d);
        
        var filaFinal = [
          fechaStr,  // A: Fecha Registro
          "",        // B: Mes (Fórmula ARRAYFORMULA en B5)
          turno,     // C: Turno
          semanaISO, // D: Semana
          diaSemana, // E: Día
          row[2],    // F: Carretillero R.
          row[3],    // G: Nº Pallets Reub.
          row[4],    // H: Carretillero C.
          row[5],    // I: Nº Compact.
          row[6],    // J: Tiempo Compact
          row[7],    // K: Carretillero NCT
          row[8],    // L: Nº Pedido
          row[9],    // M: Nº Cajas
          row[10]    // N: Tiempo NCT
        ];
        
        sheet.appendRow(filaFinal);
      }
      
      return ContentService.createTextOutput(JSON.stringify({status: "success"}))
                           .setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({status: "error", message: "Acción no reconocida"}))
                         .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: error.toString()}))
                         .setMimeType(ContentService.MimeType.JSON);
  }
}

// --- FUNCIONES AUXILIARES DE FECHA ---
function getISOWeek(date) {
  var target = new Date(date.valueOf());
  var dayNr = (date.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNr + 3);
  var firstThursday = target.valueOf();
  target.setMonth(0, 1);
  if (target.getDay() !== 4) {
    target.setMonth(0, 1 + ((4 - target.getDay() + 7) % 7));
  }
  return Math.ceil((firstThursday - target) / (7 * 86400000) + 1);
}

function getDiaSemanaEspanol(date) {
  var dias = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
  return dias[date.getDay()];
}