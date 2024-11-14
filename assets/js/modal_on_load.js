const SHOW_MODAL = false;
const MODAL_NAME = 'name_update';

window.addEventListener('load', function() {
  let modal_on_load_value = localStorage.getItem("modal_on_load")
  const modalElement = document.getElementById('modal-on-load');

  if (SHOW_MODAL && modal_on_load_value !== MODAL_NAME) {
    const bsModal = new bootstrap.Modal(modalElement)
    bsModal.show()
  }

  modalElement.addEventListener('hide.bs.modal', function() {
    localStorage.setItem("modal_on_load", MODAL_NAME);
  })
})
