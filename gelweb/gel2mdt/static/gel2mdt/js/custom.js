/*Copyright (c) 2018 Great Ormond Street Hospital for Children NHS Foundation
Trust & Birmingham Women's and Children's NHS Foundation Trust

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.*/
// // $(function () {
// //      $(".js-edit-mdt").click(function () {
// //       var btn = $(this);  // <-- HERE
// //       $.ajax({
// //         url: btn.attr("data-url"),  // <-- AND HERE
// //         type: 'get',
// //         dataType: 'json',
// //         beforeSend: function () {
// //           $("#modal-mdt").modal("show");
// //         },
// //         success: function (data) {
// //           $("#modal-mdt .modal-content").html(data.html_form);
// //         }
// //       });
// //     });
// //
// //     $("#modal-mdt").on("submit", ".js-save-mdt", function () {
// //     var form = $(this);
// //     $.ajax({
// //       url: form.attr("action"),
// //       data: form.serialize(),
// //       type: form.attr("method"),
// //       dataType: 'json',
// //       success: function (data) {
// //         if (data.form_is_valid) {
// //                 $("#mdt-table tbody").html(data.html_mdt_list);
// //                 $("#modal-mdt").modal("hide");  // <-- Close the modal
// //         }
// //         else {
// //           $("#modal-mdt .modal-content").html(data.html_form);
// //         }
// //       }
// //     });
// //     return false;
// //   });
// // });
//
// $(function () {
//
//   /* Functions */
//
//   var loadForm = function () {
//     var btn = $(this);
//     $.ajax({
//       url: btn.attr("data-url"),
//       type: 'get',
//       dataType: 'json',
//       beforeSend: function () {
//         $("#modal-mdt .modal-content").html("");
//         $("#modal-mdt").modal("show");
//       },
//       success: function (data) {
//         $("#modal-mdt .modal-content").html(data.html_form);
//       }
//     });
//   };
//
//    var variantloadForm = function () {
//     var btn = $(this);
//     $.ajax({
//       url: btn.attr("data-url"),
//       type: 'get',
//       dataType: 'json',
//       beforeSend: function () {
//         $("#modal-sample .modal-content").html("");
//         $("#modal-sample").modal("show");
//       },
//       success: function (data) {
//         $("#modal-sample .modal-content").html(data.html_form);
//       }
//     });
//   };
//
//    var sampleloadForm = function () {
//     var btn = $(this);
//     $.ajax({
//       url: btn.attr("data-url"),
//       type: 'get',
//       dataType: 'json',
//       beforeSend: function () {
//         $("#modal-novariant .modal-content").html("");
//         $("#modal-novariant").modal("show");
//       },
//       success: function (data) {
//         $("#modal-novariant .modal-content").html(data.html_form);
//       }
//     });
//   };
//
//   var saveForm = function () {
//     var form = $(this);
//     $.ajax({
//       url: form.attr("action"),
//       data: form.serialize(),
//       type: form.attr("method"),
//       dataType: 'json',
//       success: function (data) {
//         if (data.form_is_valid) {
//           $("#mdt-table tbody").html(data.html_mdt_list);
//           $("#modal-mdt").modal("hide");
//         }
//         else {
//           $("#modal-mdt .modal-content").html(data.html_form);
//         }
//       }
//     });
//     return false;
//   };
//
//   var variantsaveForm = function () {
//     var form = $(this);
//     $.ajax({
//       url: form.attr("action"),
//       data: form.serialize(),
//       type: form.attr("method"),
//       dataType: 'json',
//       success: function (data) {
//         if (data.form_is_valid) {
//           $("#samplevariant-table tbody").html(data.html_mdt_list);
//           $("#modal-sample").modal("hide");
//         }
//         else {
//           $("#modal-sample .modal-content").html(data.html_form);
//         }
//       }
//     });
//     return false;
//   };
//
//    var samplesaveForm = function () {
//     var form = $(this);
//     $.ajax({
//       url: form.attr("action"),
//       data: form.serialize(),
//       type: form.attr("method"),
//       dataType: 'json',
//       success: function (data) {
//         if (data.form_is_valid) {
//           $("#sample-table tbody").html(data.html_mdt_list);
//           $("#modal-novariant").modal("hide");
//         }
//         else {
//           $("#modal-novariant .modal-content").html(data.html_form);
//         }
//       }
//     });
//     return false;
//   };
//   /* Binding */
//
//   $("#mdt-table").on("click", ".js-edit-mdt", loadForm);
//   $("#modal-mdt").on("submit", ".js-save-mdt", saveForm);
//
//   $("#samplevariant-table").on("click", ".js-edit-variant", variantloadForm);
//   $("#modal-sample").on("submit", ".js-save-variant", variantsaveForm);
//
//   $("#sample-table").on("click", ".js-edit-sample", sampleloadForm);
//   $("#modal-novariant").on("submit", ".js-save-sample", samplesaveForm);
// });
//

function updateElementIndex(el, prefix, ndx) {
    var id_regex = new RegExp('(' + prefix + '-\\d+)');
    var replacement = prefix + '-' + ndx;
    if ($(el).attr("for")) $(el).attr("for", $(el).attr("for").replace(id_regex, replacement));
    if (el.id) el.id = el.id.replace(id_regex, replacement);
    if (el.name) el.name = el.name.replace(id_regex, replacement);
}
function cloneMore(selector, prefix) {
    var newElement = $(selector).clone(true);
    var total = $('#id_' + prefix + '-TOTAL_FORMS').val();
    newElement.find(':input').each(function() {
        var name = $(this).attr('name').replace('-' + (total-1) + '-', '-' + total + '-');
        var id = 'id_' + name;
        $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
    });
    total++;
    $('#id_' + prefix + '-TOTAL_FORMS').val(total);
    $(selector).after(newElement);
    var conditionRow = $('.form-row:not(:last)');
    conditionRow.find('.btn.add-form-row')
     .removeClass('btn-success').addClass('btn-danger')
    .removeClass('add-form-row').addClass('remove-form-row')
    .html('<span class="glyphicon glyphicon-minus" aria-hidden="true"></span>');
    return false;
}
function deleteForm(prefix, btn) {
    var total = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    if (total > 1){
        btn.closest('.form-row').remove();
        var forms = $('.form-row');
        $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
        for (var i=0, formCount=forms.length; i<formCount; i++) {
            $(forms.get(i)).find(':input').each(function() {
                updateElementIndex(this, prefix, i);
            });
        }
    }
    return false;

}$(document).on('click', '.add-form-row', function(e){
    e.preventDefault();
    cloneMore('.form-row:last', 'form');
    return false;
});
$(document).on('click', '.remove-form-row', function(e){
    e.preventDefault();
    deleteForm('form', $(this));
    return false;
});
