window.addEventListener('load', function() {
  let modal_on_load_value = localStorage.getItem("modal_on_load")
  const modalElement = document.getElementById('modal-on-load');

  if (modal_on_load_value !== 'seen') {
    const bsModal = new bootstrap.Modal(modalElement)
    bsModal.show()
  }

  modalElement.addEventListener('hide.bs.modal', function() {
    localStorage.setItem("modal_on_load", "seen");
  })
})
