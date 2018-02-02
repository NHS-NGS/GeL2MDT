// $(function () {
//      $(".js-edit-mdt").click(function () {
//       var btn = $(this);  // <-- HERE
//       $.ajax({
//         url: btn.attr("data-url"),  // <-- AND HERE
//         type: 'get',
//         dataType: 'json',
//         beforeSend: function () {
//           $("#modal-mdt").modal("show");
//         },
//         success: function (data) {
//           $("#modal-mdt .modal-content").html(data.html_form);
//         }
//       });
//     });
//
//     $("#modal-mdt").on("submit", ".js-save-mdt", function () {
//     var form = $(this);
//     $.ajax({
//       url: form.attr("action"),
//       data: form.serialize(),
//       type: form.attr("method"),
//       dataType: 'json',
//       success: function (data) {
//         if (data.form_is_valid) {
//                 $("#mdt-table tbody").html(data.html_mdt_list);
//                 $("#modal-mdt").modal("hide");  // <-- Close the modal
//         }
//         else {
//           $("#modal-mdt .modal-content").html(data.html_form);
//         }
//       }
//     });
//     return false;
//   });
// });

$(function () {

  /* Functions */

  var loadForm = function () {
    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-mdt .modal-content").html("");
        $("#modal-mdt").modal("show");
      },
      success: function (data) {
        $("#modal-mdt .modal-content").html(data.html_form);
      }
    });
  };

   var variantloadForm = function () {
    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-sample .modal-content").html("");
        $("#modal-sample").modal("show");
      },
      success: function (data) {
        $("#modal-sample .modal-content").html(data.html_form);
      }
    });
  };

   var sampleloadForm = function () {
    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-novariant .modal-content").html("");
        $("#modal-novariant").modal("show");
      },
      success: function (data) {
        $("#modal-novariant .modal-content").html(data.html_form);
      }
    });
  };

  var saveForm = function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#mdt-table tbody").html(data.html_mdt_list);
          $("#modal-mdt").modal("hide");
        }
        else {
          $("#modal-mdt .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };

  var variantsaveForm = function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#samplevariant-table tbody").html(data.html_mdt_list);
          $("#modal-sample").modal("hide");
        }
        else {
          $("#modal-sample .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };

   var samplesaveForm = function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#sample-table tbody").html(data.html_mdt_list);
          $("#modal-novariant").modal("hide");
        }
        else {
          $("#modal-novariant .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };
  /* Binding */

  $("#mdt-table").on("click", ".js-edit-mdt", loadForm);
  $("#modal-mdt").on("submit", ".js-save-mdt", saveForm);

  $("#samplevariant-table").on("click", ".js-edit-variant", variantloadForm);
  $("#modal-sample").on("submit", ".js-save-variant", variantsaveForm);

  $("#sample-table").on("click", ".js-edit-sample", sampleloadForm);
  $("#modal-novariant").on("submit", ".js-save-sample", samplesaveForm);
});