document.addEventListener("DOMContentLoaded", () => {

  // Loading no botão de login
const loginForm = document.querySelector("form");
const loginBtn = document.getElementById("login-btn");

if (loginForm && loginBtn) {
  loginForm.addEventListener("submit", () => {
    loginBtn.disabled = true;
    loginBtn.innerText = "Entrando...";
  });
}

  // 👁 Mostrar senha
  document.querySelectorAll(".toggle-password").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.target);
      const icon = btn.querySelector("i");

      if (input.type === "password") {
        input.type = "text";
        icon.classList.replace("bi-eye", "bi-eye-slash");
      } else {
        input.type = "password";
        icon.classList.replace("bi-eye-slash", "bi-eye");
      }
    });
  });

  // ✅ Validação simples
  document.querySelectorAll("input").forEach(input => {
    input.addEventListener("input", () => {
      if (input.checkValidity()) {
        input.classList.remove("is-invalid");
        input.classList.add("is-valid");
      } else {
        input.classList.remove("is-valid");
      }
    });
  });

});