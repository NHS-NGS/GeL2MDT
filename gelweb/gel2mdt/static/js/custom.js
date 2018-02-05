

$(function () {

  /* Functions */

  var variantloadForm = function () {
    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-variant-mdt .modal-content").html("");
        $("#modal-variant-mdt").modal("show");
      },
      success: function (data) {
        $("#modal-variant-mdt .modal-content").html(data.html_form);
      }
    });
  };


   var probandloadForm = function () {
    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-proband-mdt .modal-content").html("");
        $("#modal-proband-mdt").modal("show");
      },
      success: function (data) {
        $("#modal-proband-mdt .modal-content").html(data.html_form);
      }
    });
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
          $("#mdt-variant-table tbody").html(data.html_mdt_list);
          $("#modal-variant-mdt").modal("hide");
        }
        else {
          $("#modal-variant-mdt .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };

   var probandsaveForm = function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          $("#mdt-proband-table tbody").html(data.html_mdt_list);
          $("#modal-proband-mdt").modal("hide");
        }
        else {
          $("#modal-proband-mdt .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };
  /* Binding */

  $("#mdt-variant-table").on("click", ".js-edit-mdt-variant", variantloadForm);
  $("#modal-variant-mdt").on("submit", ".js-save-mdt-variant", variantsaveForm);

  $("#mdt-proband-table").on("click", ".js-edit-mdt-proband", probandloadForm);
  $("#modal-proband-mdt").on("submit", ".js-save-mdt-proband", probandsaveForm);
});