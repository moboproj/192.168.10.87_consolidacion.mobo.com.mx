$(document).ready(function () {
  // Mapeo de números de cuenta a identificadores de elementos HTML
  const cuentaElementoMap = {
    110543411: "#bbvaFooter",
    110579440: "#amexFooter",
    4045893245: "#hsbcFooter",
    4067964031: "#otrobbvaFooter",
  };

  // Función para formatear números
  function formatearNumero(numero) {
    return numero.toLocaleString("es-ES", { minimumFractionDigits: 2 });
  }

  // Función para procesar los datos y actualizar los elementos HTML
  function actualizarElementos(data) {
    try {
      data.forEach(function (entry) {
        var monto = formatearNumero(entry.Total_dia);
        var nuCuenta = entry.NuCuenta;
        var elemento = cuentaElementoMap[nuCuenta];

        // Log para asegurarse de que se esté actualizando el elemento correcto
        console.log("Actualizando elemento para la cuenta:", nuCuenta);

        // Actualizar los elementos HTML según el número de cuenta
        if (elemento) {
          $(elemento).text("Monto banco: $" + monto);
        }
      });
    } catch (error) {
      console.error("Error al procesar los datos:", error);
    }
  }

  $.ajax({
    url: Sum_extra,
    type: "GET",
    dataType: "json",
    success: function (data) {
      console.log("Datos recibidos del servidor:", data);

      // Procesar los datos recibidos y actualizar los elementos HTML
      actualizarElementos(data);

      const lastUpdate = new Date();
      $(".card-footer").text(
        "Última Actualización: " + lastUpdate.toLocaleDateString()
      );
    },
    error: function (error) {
      console.log("Error en la solicitud Ajax: ", error);
      console.log("Respuesta del servidor:", error.responseText);
      $(".card-footer").text(
        "Error al cargar los datos. Por favor, inténtalo de nuevo más tarde."
      );
    },
  });
});

function submitForm() {
  var fechaExtrac = $("#fecextrac").val();
  var FecextFin = $("#FecextFin").val();

  if (!fechaExtrac || !FecextFin) {
    var errorMessage =
      !fechaExtrac && !FecextFin
        ? "Ambos campos están vacíos. Por favor, rellénalos."
        : !fechaExtrac
        ? "El campo Fecha inicio está vacío. Por favor, rellénalo."
        : "El campo Fecha fin está vacío. Por favor, rellénalo.";
    errorajax(errorMessage);
  } else if (fechaExtrac > FecextFin) {
    errorajax("La fecha de inicio no puede ser mayor que la fecha de fin.");
  } else if (FecextFin < fechaExtrac) {
    errorajax("La fecha de fin no puede ser menor que la fecha de inicio.");
  } else {
    Loading();
    // Convertir las cadenas de fecha a objetos Date
    var fechaExtracDate = new Date(fechaExtrac);
    var FecextFinDate = new Date(FecextFin);

    // Restar un día a cada fecha
    fechaExtracDate.setDate(fechaExtracDate.getDate() - 1);
    FecextFinDate.setDate(FecextFinDate.getDate() - 1);

    // Guardar las fechas actualizadas en nuevas variables
    var fechaExtracActualizada = fechaExtracDate.toISOString().split("T")[0];
    var FecextFinActualizada = FecextFinDate.toISOString().split("T")[0];
    console.log(FecextFinActualizada);
    console.log(fechaExtracActualizada);

    if (fechaExtrac) {
      $.ajax({
        url: newDashboardUrl, // usar la variable generada
        method: "GET",
        data: {
          fecextrac: fechaExtrac,
          FecextFin: FecextFin,
        },
        success: function (response) {
          $("#tabla-tarjetas tbody").empty();
          response.datos_original.forEach(function (dato) {
            let porcentajeNumerico = parseFloat(dato.porcentaje);
            var row =
              "<tr>" +
              "<td>" +
              dato.NuCuenta +
              "</td>" +
              "<td>" +
              fechaExtrac +
              " a " +
              FecextFin +
              "</td>" +
              "<td>" +
              formatCurrency(dato.Abono) +
              "</td>" +
              "<td>" +
              porcentajeNumerico.toFixed(1) +
              " %" +
              "</td>" +
              "</tr>";
            $("#tabla-tarjetas tbody").append(row);
          });
          $("#tabla-extractos tbody").empty();
          response.datos_reducida.forEach(function (dato) {
            let porcentajeNumerico = parseFloat(dato.porcentaje);
            var row =
              "<tr>" +
              "<td>" +
              dato.origen +
              "</td>" +
              "<td>" +
              fechaExtracActualizada +
              " a " +
              FecextFinActualizada +
              "</td>" +
              "<td>" +
              formatCurrency(dato.monto) +
              "</td>" +
              "<td>" +
              porcentajeNumerico.toFixed(1) +
              " %" +
              "</td>" +
              "</tr>";
            $("#tabla-extractos tbody").append(row);
          });
          showTable("table1");
        },
        error: function (error) {
          console.error("Error:", error);
        },
      });
    } else {
      alert("Por favor, seleccione una fecha.");
    }
  }
}
function submitForm2() {
  var fechaExtrac = $("#fecextrac").val();
  if (fechaExtrac) {
    $.ajax({
      //  url: '/EfectivoDashbord/',
      url: '{% url "MAIN:EfectivoDashbord"%}',
      method: "GET",
      data: { fecextrac: fechaExtrac },
      success: function (response) {
        console.log(response); // Verificar la estructura de la respuesta

        // Vaciar tablas antes de llenarlas
        $("#tabla-efectivo tbody").empty();
        $("#tabla-extractos-Efectivo tbody").empty();

        // Verificar y llenar datos_original
        if (response.datos_original && Array.isArray(response.datos_original)) {
          response.datos_original.forEach(function (dato) {
            var row =
              "<tr>" +
              "<td>" +
              dato.NuCuenta +
              "</td>" +
              "<td>" +
              dato.Fecha_Op +
              "</td>" +
              "<td>" +
              formatCurrency(dato.Abono) +
              "</td>" +
              "<td>0</td>" +
              "</tr>";
            $("#tabla-efectivo tbody").append(row);
          });
        } else {
          console.error("data_original no está definido o no es un array");
        }

        // Verificar y llenar datos_reducida
        if (response.datos_reducida && Array.isArray(response.datos_reducida)) {
          response.datos_reducida.forEach(function (dato) {
            var row =
              "<tr>" +
              "<td>" +
              dato.origen +
              "</td>" +
              "<td>" +
              dato.fecha +
              "</td>" +
              "<td>" +
              formatCurrency(dato.total) +
              "</td>" +
              "</tr>";
            $("#tabla-extractos-Efectivo tbody").append(row);
          });
        } else {
          console.error("datos_reducida no está definido o no es un array");
        }

        showTable("table2");
      },
      error: function (error) {
        console.error("Error:", error);
      },
    });
  } else {
    alert("Por favor, seleccione una fecha.");
  }
}

function showTable(tableId) {
  const tablesContainer = document.getElementById("tables");
  const table = document.getElementById(tableId);
  tablesContainer.prepend(table); // Mueve la tabla al principio del contenedor
  table.classList.add("visible"); // Hace visible la tabla
}

function clearTables() {
  $("#table1 tbody").empty();
  $("#table2 tbody").empty();
  document.getElementById("table1").classList.remove("visible");
  document.getElementById("table2").classList.remove("visible");
}

document.getElementById("fecextrac").addEventListener("change", clearTables);

function formatCurrency(amount) {
  return (
    "$" +
    parseFloat(amount)
      .toFixed(2)
      .replace(/\d(?=(\d{3})+\.)/g, "$&,")
  );
}

function tarjetNum() {
  const select = document.getElementById("mi-select");
  const selectedValue = select.options[select.selectedIndex].value;

  if (selectedValue !== "opcion0") {
    $.ajax({
      url: totalesXtienda, // Asegúrate de que esta URL coincide con tu configuración de Django
      type: "GET",
      dataType: "json",
      data: {
        numero_tienda: selectedValue,
      },
      success: function (data) {
        console.log(data);

        // Limpiar el cuerpo de la tabla
        const tableBody = $("#dataTableBody");
        tableBody.empty();

        // Destruir cualquier instancia existente de DataTable
        if ($.fn.dataTable.isDataTable("#dataTable")) {
          $("#dataTable").DataTable().clear().destroy();
        }

        // Agregar las nuevas filas al cuerpo de la tabla
        data.forEach((fila) => {
          const newRow = $("<tr>");
          newRow.append(`<td>${fila.idtbl_ExtractosBancarios}</td>`);
          newRow.append(`<td>${fila.NuCuenta}</td>`);
          newRow.append(`<td>${fila.Fecha_Op}</td>`);
          newRow.append(`<td>${fila.Tipo_trans}</td>`);
          newRow.append(`<td>${fila.Ref_ampl}</td>`);
          newRow.append(`<td>${fila.No_Cl}</td>`);
          newRow.append(`<td>${fila.Abono}</td>`);
          newRow.append(`<td>${fila.Cargo}</td>`);
          tableBody.append(newRow);
        });

        // Inicializar DataTable con opciones de paginación
        $("#dataTable").DataTable({
          pageLength: 10, // Número de filas por página
          destroy: true, // Permitir reinicialización de la tabla
        });
      },
      error: function (error) {
        console.log("Error en la solicitud tablas: ", error);
        try {
          $("#mensajeError").text(JSON.parse(error.responseText).error);
        } catch (e) {
          $("#mensajeError").text(
            "Error desconocido al procesar la solicitud."
          );
        }
      },
    });
  } else {
    alert("Por favor, seleccione una opción válida.");
  }
}
