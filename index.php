<?php
// Logo del centro (misma ruta que OpenEMR)
$logo = "/sites/default/images/logo_centro.png";
$logo_fs = $_SERVER['DOCUMENT_ROOT'] . $logo;
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Registro de Paciente</title>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no" />

  <style>
    :root{
      --bg:#f2f4f7;
      --card:#ffffff;
      --text:#111827;
      --muted:#6b7280;
      --line:#e5e7eb;
      --primary:#2c7be5;
      --primaryDark:#1f5fb6;
      --danger:#d1242f;
      --radius:16px;
    }

    *{ box-sizing:border-box; }
    body{
      margin:0;
      font-family: Arial, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background:var(--bg);
      color:var(--text);
    }

    .page{
      max-width: 820px;
      margin: 0 auto;
      padding: 18px 14px 28px;
    }

    .card{
      background:var(--card);
      border-radius: var(--radius);
      padding: 18px;
      box-shadow: 0 6px 18px rgba(0,0,0,.06);
    }

    .brand{
      display:flex;
      flex-direction:column;
      align-items:center;
      text-align:center;
      gap:10px;
      padding-bottom: 14px;
      border-bottom:1px solid var(--line);
      margin-bottom: 16px;
    }

    .brand img{
      max-width: 240px;
      width: 70%;
      height:auto;
      display:block;
    }

    .brand .info{
      font-size: 14px;
      line-height: 1.35;
      color: var(--muted);
    }

    h1{
      margin: 0 0 12px 0;
      font-size: 22px;
      letter-spacing: .2px;
    }

    .hint{
      margin-top: -8px;
      margin-bottom: 14px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.35;
    }

    label{
      display:block;
      font-size: 16px;
      margin: 10px 0 8px;
      font-weight: 700;
    }

    input, textarea, select{
      width:100%;
      padding: 14px 14px;
      font-size: 18px;
      border: 2px solid var(--line);
      border-radius: 12px;
      outline: none;
      background:#fff;
    }

    input:focus, textarea:focus, select:focus{
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(44,123,229,.15);
    }

    textarea{
      min-height: 110px;
      resize: vertical;
    }

    .grid{
      display:grid;
      grid-template-columns: 1fr;
      gap: 12px;
    }

    @media (min-width: 700px){
      .grid-2{ grid-template-columns: 1fr 1fr; }
      .grid-3{ grid-template-columns: 1fr 1fr 1fr; }
    }

    .readonly{
      background:#f9fafb;
    }

    .actions{
      margin-top: 16px;
      display:flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .btn{
      appearance:none;
      border:none;
      border-radius: 14px;
      padding: 16px 18px;
      font-size: 20px;
      font-weight: 800;
      cursor: pointer;
      flex: 1 1 240px;
    }

    .btn-primary{
      background: var(--primary);
      color:#fff;
    }
    .btn-primary:active{ background: var(--primaryDark); }

    .btn-secondary{
      background:#eef2ff;
      color:#1f2937;
    }

    .section-title{
      margin-top: 18px;
      font-size: 18px;
      font-weight: 800;
      padding-top: 14px;
      border-top: 1px solid var(--line);
    }

    .hidden{ display:none; }

    .pill{
      display:inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background:#f3f4f6;
      color:#374151;
      font-size: 13px;
      margin-top: 8px;
    }

    .footer-note{
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
      text-align:center;
    }
  </style>
</head>

<body>
  <div class="page">
    <div class="card">

      <div class="brand">
        <?php if (file_exists($logo_fs)) { ?>
          <img src="<?php echo htmlspecialchars($logo); ?>" alt="Centro Neuropsicológico Saavedra">
          <div class="info">
            Psje. Mejia # 6 (Av. Aniceto Arce #824), Cochabamba, Bolivia<br>
            Telf: 4 4535184 &nbsp;&nbsp; 77918497<br>
            psicocentro.saavedra@gmail.com
          </div>
        <?php } else { ?>
          <div class="info"><b>Centro Neuropsicológico Saavedra</b></div>
        <?php } ?>
      </div>

      <h1>Registro de Paciente</h1>
      <div class="hint">
        Por favor complete los datos. Al finalizar, presione <b>Enviar</b> y entregue la tablet en recepción.
      </div>

      <form action="guardar.php" method="POST" autocomplete="off">

        <label>Nombres del paciente</label>
        <input type="text" name="nombres" required inputmode="text" autocapitalize="words" />

        <div class="grid grid-2">
          <div>
            <label>Fecha de nacimiento</label>
            <input type="date" name="fecha_nacimiento" id="fecha_nacimiento" required />
          </div>
          <div>
            <label>Edad</label>
            <input type="number" name="edad" id="edad" class="readonly" readonly />
            <span class="pill" id="pill_menor" style="display:none;">Menor de edad</span>
          </div>
        </div>

        <label>Teléfono</label>
        <input type="tel" name="telefono" required inputmode="tel" placeholder="Ej: 7xxxxxxx" />

        <label>Motivo de consulta</label>
        <textarea name="motivo_consulta" required placeholder="Describa brevemente el motivo..."></textarea>

        <div class="grid grid-2">
          <div>
            <label>Derivación</label>
            <input type="text" name="derivacion" placeholder="Ej: colegio, doctor, familiar, etc." />
          </div>
          <div>
            <label>Evaluación</label>
            <input type="text" name="evaluacion" placeholder="Ej: neuropsicológica, WISC, TOVA, etc." />
          </div>
        </div>

        <div class="grid grid-2">
          <div>
            <label>¿Es menor de edad?</label>
            <select name="es_menor" id="es_menor">
              <option value="0" selected>No</option>
              <option value="1">Sí</option>
            </select>
          </div>
          <div></div>
        </div>

        <div id="bloque_tutores" class="hidden">
          <div class="section-title">Datos del padre y madre</div>

          <div class="grid grid-2">
            <div>
              <label>Padre (nombre)</label>
              <input type="text" name="padre_nombre" id="padre_nombre" autocapitalize="words" />
            </div>
            <div>
              <label>Padre (teléfono)</label>
              <input type="tel" name="padre_telefono" id="padre_telefono" inputmode="tel" />
            </div>
          </div>

          <div class="grid grid-2">
            <div>
              <label>Madre (nombre)</label>
              <input type="text" name="madre_nombre" id="madre_nombre" autocapitalize="words" />
            </div>
            <div>
              <label>Madre (teléfono)</label>
              <input type="tel" name="madre_telefono" id="madre_telefono" inputmode="tel" />
            </div>
          </div>
        </div>

        <div class="actions">
          <button class="btn btn-primary" type="submit">Enviar</button>
          <button class="btn btn-secondary" type="reset" id="btn_limpiar">Limpiar</button>
        </div>

        <div class="footer-note">
          Si necesita ayuda, solicite apoyo a recepción.
        </div>
      </form>
    </div>
  </div>

<script>
  function calcularEdad(fechaStr) {
    if (!fechaStr) return "";
    const hoy = new Date();
    const nac = new Date(fechaStr + "T00:00:00");
    let edad = hoy.getFullYear() - nac.getFullYear();
    const m = hoy.getMonth() - nac.getMonth();
    if (m < 0 || (m === 0 && hoy.getDate() < nac.getDate())) edad--;
    return (edad >= 0 ? edad : "");
  }

  const fecha = document.getElementById("fecha_nacimiento");
  const edad = document.getElementById("edad");
  const esMenor = document.getElementById("es_menor");
  const bloque = document.getElementById("bloque_tutores");
  const pillMenor = document.getElementById("pill_menor");
  const btnLimpiar = document.getElementById("btn_limpiar");

  function setMenorUI(isMenor) {
    if (isMenor) {
      esMenor.value = "1";
      bloque.classList.remove("hidden");
      pillMenor.style.display = "inline-block";
    } else {
      esMenor.value = "0";
      bloque.classList.add("hidden");
      pillMenor.style.display = "none";
    }
  }

  fecha.addEventListener("change", () => {
    const e = calcularEdad(fecha.value);
    edad.value = e;

    if (e !== "" && parseInt(e, 10) < 18) {
      setMenorUI(true);
    } else if (esMenor.value !== "1") {
      setMenorUI(false);
    }
  });

  esMenor.addEventListener("change", () => {
    setMenorUI(esMenor.value === "1");
  });

  btnLimpiar.addEventListener("click", () => {
    setTimeout(() => {
      edad.value = "";
      setMenorUI(false);
    }, 0);
  });

  // Evita que Enter envíe el formulario accidentalmente desde teclado virtual
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.tagName !== "TEXTAREA") {
      e.preventDefault();
    }
  });
</script>

</body>
</html>