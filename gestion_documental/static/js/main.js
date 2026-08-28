/**
 * SIGEA — JavaScript Principal
 */
document.addEventListener('DOMContentLoaded', function() {

  // === Auto-dismiss alerts ===
  document.querySelectorAll('.alert').forEach(function(a) {
    setTimeout(function() { a.style.transition='opacity .5s'; a.style.opacity='0'; setTimeout(function(){a.remove();},500); }, 5000);
  });

  // === Active sidebar link ===
  var currentPath = window.location.pathname;
  var currentFull = window.location.pathname + window.location.search;
  
  document.querySelectorAll('.sidebar-link').forEach(function(link) {
    var linkHref = link.getAttribute('href');
    if (linkHref === currentFull || linkHref === currentPath) {
      link.classList.add('active');
    }
  });

  // === Toggle password visibility ===
  document.querySelectorAll('.toggle-password').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var input = this.closest('.input-wrapper').querySelector('input');
      if (input.type === 'password') { input.type = 'text'; this.textContent = '🙈'; }
      else { input.type = 'password'; this.textContent = '👁️'; }
    });
  });

  // === Token 6-digit inputs ===
  var tokenInputs = document.querySelectorAll('.token-input');
  var tokenHidden = document.getElementById('token-hidden');
  var tokenBtn = document.getElementById('token-submit-btn');
  if (tokenInputs.length === 6) {
    tokenInputs.forEach(function(inp, idx) {
      inp.addEventListener('input', function() {
        this.value = this.value.replace(/\D/g, '').slice(0,1);
        if (this.value && idx < 5) tokenInputs[idx+1].focus();
        updateTokenHidden();
      });
      inp.addEventListener('keydown', function(e) {
        if (e.key === 'Backspace' && !this.value && idx > 0) { tokenInputs[idx-1].focus(); tokenInputs[idx-1].value = ''; updateTokenHidden(); }
      });
      inp.addEventListener('paste', function(e) {
        e.preventDefault();
        var data = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '').slice(0,6);
        for (var i=0; i<data.length && i<6; i++) tokenInputs[i].value = data[i];
        if (data.length > 0) tokenInputs[Math.min(data.length,5)].focus();
        updateTokenHidden();
      });
    });
    function updateTokenHidden() {
      var val = '';
      tokenInputs.forEach(function(i){ val += i.value; });
      if (tokenHidden) tokenHidden.value = val;
      if (tokenBtn) tokenBtn.disabled = val.length < 6;
    }
  }

  // === Countdown timer (3:00) ===
  var countdownEl = document.getElementById('countdown-timer');
  if (countdownEl) {
    var total = 180; // 3 minutes
    var interval = setInterval(function() {
      total--;
      if (total <= 0) {
        clearInterval(interval);
        countdownEl.textContent = '0:00';
        countdownEl.style.color = '#ef4444';
        if (tokenBtn) { tokenBtn.disabled = true; tokenBtn.textContent = 'Token expirado'; }
      } else {
        var m = Math.floor(total/60);
        var s = total % 60;
        countdownEl.textContent = m + ':' + (s < 10 ? '0' : '') + s;
      }
    }, 1000);
  }

  // === Password requirements validation ===
  var newPwd = document.getElementById('new-password');
  if (newPwd) {
    var reqLen = document.getElementById('req-length');
    var reqUpper = document.getElementById('req-uppercase');
    var reqSpecial = document.getElementById('req-special');
    newPwd.addEventListener('input', function() {
      var v = this.value;
      if (reqLen) { if(v.length >= 8) reqLen.classList.add('valid'); else reqLen.classList.remove('valid'); }
      if (reqUpper) { if(/[A-Z]/.test(v)) reqUpper.classList.add('valid'); else reqUpper.classList.remove('valid'); }
      if (reqSpecial) { if(/[!@#$%^&*]/.test(v)) reqSpecial.classList.add('valid'); else reqSpecial.classList.remove('valid'); }
    });
  }

  // === Drag & Drop upload zone ===
  var zone = document.getElementById('upload-zone');
  var fileInput = document.getElementById('id_archivo');
  if (zone && fileInput) {
    zone.addEventListener('click', function() { fileInput.click(); });
    zone.addEventListener('dragover', function(e) { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', function() { zone.classList.remove('dragover'); });
    zone.addEventListener('drop', function(e) {
      e.preventDefault(); zone.classList.remove('dragover');
      if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; updateFileName(e.dataTransfer.files[0].name); }
    });
    fileInput.addEventListener('change', function() { if(this.files.length) updateFileName(this.files[0].name); });
    function updateFileName(name) {
      var txt = zone.querySelector('.upload-zone-text');
      if(txt) txt.innerHTML = '📎 <strong>' + name + '</strong>';
    }
  }

  // === Real-time Navbar Search ===
  const searchInput = document.getElementById('navbarSearchInput');
  const resultsDiv = document.getElementById('searchResults');

  if (searchInput && resultsDiv) {
    let debounceTimer;

    searchInput.addEventListener('input', function() {
      clearTimeout(debounceTimer);
      const query = this.value.trim();

      if (query.length < 2) {
        resultsDiv.style.display = 'none';
        resultsDiv.innerHTML = '';
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`/documentos/api/buscar/?q=${encodeURIComponent(query)}`)
          .then(response => response.json())
          .then(data => {
            resultsDiv.innerHTML = '';
            if (data.results && data.results.length > 0) {
              data.results.forEach(item => {
                const a = document.createElement('a');
                a.href = item.url;
                a.className = 'search-result-item';
                
                // Resaltar coincidencia
                const regex = new RegExp(`(${query})`, 'gi');
                const highlighted = item.titulo.replace(regex, '<strong>$1</strong>');
                
                a.innerHTML = `<span>📄</span> ${highlighted}`;
                resultsDiv.appendChild(a);
              });
              resultsDiv.style.display = 'block';
            } else {
              resultsDiv.innerHTML = '<div class="search-result-item">No se encontraron resultados</div>';
              resultsDiv.style.display = 'block';
            }
          })
          .catch(err => console.error('Error en búsqueda:', err));
      }, 300);
    });

    // Cerrar resultados al hacer clic fuera
    document.addEventListener('click', function(e) {
      if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
        resultsDiv.style.display = 'none';
      }
    });

    // Mostrar de nuevo si el input gana foco y tiene texto
    searchInput.addEventListener('focus', function() {
      if (this.value.trim().length >= 2 && resultsDiv.children.length > 0) {
        resultsDiv.style.display = 'block';
      }
    });
  }
});

// === UI/UX REFACTOR: Mobile Sidebar Toggle ===
document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');
    const headerNav = document.querySelector('.header-nav');
    
    if (mobileMenuBtn && headerNav) {
        mobileMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            headerNav.classList.toggle('nav-open');
        });

        if (closeSidebarBtn) {
            closeSidebarBtn.addEventListener('click', () => {
                headerNav.classList.remove('nav-open');
            });
        }

        document.addEventListener('click', (e) => {
            if (headerNav.classList.contains('nav-open') && 
                !headerNav.contains(e.target) && 
                !mobileMenuBtn.contains(e.target)) {
                headerNav.classList.remove('nav-open');
            }
        });
    }
});
