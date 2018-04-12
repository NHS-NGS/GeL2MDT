

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

  var relativeloadForm = function () {
    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-relative .modal-content").html("");
        $("#modal-relative").modal("show");
      },
      success: function (data) {
        $("#modal-relative .modal-content").html(data.html_form);
      }
    });
  };

   var relativesaveForm = function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          window.location.reload();
          $("#modal-relative").modal("hide");

        }
        else {
          $("#modal-relative .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  };
  $("#mdt-variant-table").on("click", ".js-edit-mdt-variant", variantloadForm);
  $("#modal-variant-mdt").on("submit", ".js-save-mdt-variant", variantsaveForm);

  $("#mdt-proband-table").on("click", ".js-edit-mdt-proband", probandloadForm);
  $("#modal-proband-mdt").on("submit", ".js-save-mdt-proband", probandsaveForm);

  $("#relative-table").on("click", ".js-edit-relative", relativeloadForm);
  $("#modal-relative").on("submit", ".js-save-relative", relativesaveForm);
});