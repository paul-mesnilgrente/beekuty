$(function() {
  let modal_on_load_value = localStorage.getItem("modal_on_load")

  if (modal_on_load_value !== 'seen') {
    $('#modal-on-load').modal('show')
  }

  $('#modal-on-load').on('hide.bs.modal', function() {
    localStorage.setItem("modal_on_load", "seen");
  })
})
