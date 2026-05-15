<?php
// --- DB ---
$config = require __DIR__ . '/config.local.php';

$conexion = new mysqli(
    $config['db_host'],
    $config['db_user'],
    $config['db_pass'],
    $config['db_name']
);
if ($conexion->connect_error) { die("Error de conexión: " . $conexion->connect_error); }

function post($k) { return isset($_POST[$k]) ? trim($_POST[$k]) : null; }

// --- Datos del formulario ---
$nombres          = post('nombres');
$fecha_nacimiento = post('fecha_nacimiento');
$edad             = post('edad');
$telefono         = post('telefono');
$motivo           = post('motivo_consulta');
$derivacion       = post('derivacion');
$evaluacion       = post('evaluacion');
$es_menor         = (post('es_menor') === "1") ? 1 : 0;

$padre_nombre     = $es_menor ? post('padre_nombre') : null;
$padre_telefono   = $es_menor ? post('padre_telefono') : null;
$madre_nombre     = $es_menor ? post('madre_nombre') : null;
$madre_telefono   = $es_menor ? post('madre_telefono') : null;

// --- Insert ---
$sql = "INSERT INTO registros_pacientes
(nombres, fecha_nacimiento, edad, telefono, motivo_consulta, derivacion, evaluacion, es_menor,
 padre_nombre, padre_telefono, madre_nombre, madre_telefono)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

$stmt = $conexion->prepare($sql);
$stmt->bind_param(
  "ssissssissss",
  $nombres,
  $fecha_nacimiento,
  $edad,
  $telefono,
  $motivo,
  $derivacion,
  $evaluacion,
  $es_menor,
  $padre_nombre,
  $padre_telefono,
  $madre_nombre,
  $madre_telefono
);

$ok = $stmt->execute();

// --- Logo ---
$logo = "/sites/default/images/logo_centro.png";
$logo_fs = $_SERVER['DOCUMENT_ROOT'] . $logo;
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Registro</title>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no" />
  <style>
    :root{
      --bg:#f2f4f7; --card:#fff; --text:#111827; --muted:#6b7280;
      --line:#e5e7eb; --ok:#1f883d; --bad:#d1242f;
      --radius:16px;
    }
    body{ margin:0; font-family: Arial, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:var(--bg); color:var(--text); }
    .page{ max-width:720px; margin:0 auto; padding:18px 14px 28px; }
    .card{ background:var(--card); border-radius:var(--radius); padding:18px; box-shadow:0 6px 18px rgba(0,0,0,.06); text-align:center; }
    .brand{ display:flex; flex-direction:column; align-items:center; gap:10px; padding-bottom:14px; border-bottom:1px solid var(--line); margin-bottom:16px; }
    .brand img{ max-width:240px; width:70%; height:auto; display:block; }
    .brand .info{ font-size:14px; line-height:1.35; color:var(--muted); }
    .icon{
      width:78px; height:78px; border-radius:999px; display:inline-flex; align-items:center; justify-content:center;
      margin: 8px auto 12px; font-size:42px; color:#fff;
    }
    h1{ margin:0; font-size:24px; }
    .msg{ margin-top:10px; font-size:16px; color:var(--muted); line-height:1.45; }
    .box{
      margin: 14px auto 0; max-width:520px; text-align:left; background:#f9fafb;
      border:1px solid var(--line); border-radius:14px; padding:14px;
      font-size:15px; color:#374151;
    }
    .row{ display:flex; justify-content:space-between; gap:12px; padding:8px 0; border-bottom:1px dashed #e5e7eb; }
    .row:last-child{ border-bottom:none; }
    .k{ color:#6b7280; font-weight:700; }
    .v{ font-weight:800; }
    .count{
      margin-top: 14px; display:inline-block; padding:10px 12px; border-radius:999px;
      background:#eef2ff; color:#1f2937; font-weight:800; font-size:14px;
    }
    .small{ margin-top:10px; color:var(--muted); font-size:13px; }
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

      <?php if ($ok) { ?>
        <div class="icon" style="background:var(--ok);">✓</div>
        <h1>Registro enviado</h1>
        <div class="msg">
          Gracias. Por favor entregue la tablet en recepción.
        </div>

        <div class="box">
          <div class="row"><div class="k">Paciente</div><div class="v"><?php echo htmlspecialchars($nombres); ?></div></div>
          <div class="row"><div class="k">Teléfono</div><div class="v"><?php echo htmlspecialchars($telefono); ?></div></div>
          <div class="row"><div class="k">Fecha de nacimiento</div><div class="v"><?php echo htmlspecialchars($fecha_nacimiento); ?></div></div>
          <div class="row"><div class="k">Edad</div><div class="v"><?php echo htmlspecialchars($edad); ?></div></div>
        </div>

        <div class="count">Volviendo al formulario en <span id="sec">10</span> segundos…</div>
        <div class="small">Si no vuelve automáticamente, avise a recepción.</div>

        <script>
          let s = 6;
          const el = document.getElementById("sec");
          const t = setInterval(() => {
            s--;
            el.textContent = s;
            if (s <= 0) {
              clearInterval(t);
              window.location.href = "index.php";
            }
          }, 1000);
        </script>

      <?php } else { ?>
        <div class="icon" style="background:var(--bad);">!</div>
        <h1>No se pudo guardar</h1>
        <div class="msg">
          Ocurrió un problema al registrar los datos. Por favor avise a recepción.
        </div>
        <div class="small">Puede intentar nuevamente desde el formulario.</div>
        <div class="count" style="background:#fee2e2;">Volviendo al formulario…</div>
        <script>
          setTimeout(() => { window.location.href = "index.php"; }, 5000);
        </script>
      <?php } ?>

    </div>
  </div>
</body>
</html>