<?php
$config = require __DIR__ . '/../config.local.php';

$conexion = new mysqli(
    $config['db_host'],
    $config['db_user'],
    $config['db_pass'],
    $config['db_name']
);
if ($conexion->connect_error) { die("Error de conexión: " . $conexion->connect_error); }

$result = $conexion->query("SELECT id, fecha_registro, nombres, telefono, motivo_consulta, derivacion, evaluacion, edad,
                                   es_menor, padre_nombre, padre_telefono, madre_nombre, madre_telefono,
                                   subido_openemr, fecha_subido
                            FROM registros_pacientes
                            ORDER BY fecha_registro DESC
                            LIMIT 200");
?>

<?php
$logo = "/sites/default/images/logo_centro.png";
$logo_fs = $_SERVER['DOCUMENT_ROOT'] . $logo;
?>

<!DOCTYPE html>
<html>
<head>
  <title>Recepción - Registros Kiosko</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial; background:#f2f2f2; padding:16px; }
    .wrap { background:#fff; padding:16px; border-radius:10px; }
    table { width:100%; border-collapse: collapse; }
    th, td { border-bottom:1px solid #ddd; padding:10px; text-align:left; vertical-align: top; }
    th { background:#fafafa; position: sticky; top: 0; }
    .ok { color: #1a7f37; font-weight: bold; }
    .pend { color: #b54708; font-weight: bold; }
    button { padding:8px 12px; border:none; border-radius:6px; cursor:pointer; }
    .btnok { background:#1f883d; color:#fff; }
    .btnundo { background:#57606a; color:#fff; }
    .btndel { background:#d1242f; color:#fff; }
    .small { font-size: 12px; color:#444; }
    .topbar { display:flex; align-items:baseline; justify-content:space-between; gap:12px; flex-wrap:wrap; }
    .header { display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-bottom:12px; }
    .logoBox { text-align:center; }
    .logoBox img { max-width:220px; height:auto; display:block; margin:0 auto; }
    .logoText { text-align:center; font-size:12px; line-height:1.4; margin-top:6px; color:#444; }
  </style>
</head>
<body>

<div class="wrap">

  <?php if (file_exists($logo_fs)) { ?>
    <div class="header">
      <div class="logoBox">
        <img src="<?php echo htmlspecialchars($logo); ?>" alt="Logo Centro">
        <div class="logoText">
          Psje. Mejia # 6 (Av. Aniceto Arce #824), Cochabamba, Bolivia<br>
          Telf: 4 4535184 &nbsp;&nbsp; 77918497<br>
          psicocentro.saavedra@gmail.com
        </div>
        
      </div>

      
    </div>
    <div style="text-align:center;">
        <h2 style="margin:0;">Recepción</h2>
        <div class="small" style="margin-top:6px;">Fecha de hoy: <b><?php echo date("Y-m-d"); ?></b></div>
      </div>
    </div>
  <?php } else { ?>
    <div class="topbar">
      <h2>Recepción</h2>
      <div class="small">Fecha de hoy: <b><?php echo date("Y-m-d"); ?></b></div>
    </div>
  <?php } ?>

  <br>

  <table>
    <thead>
      <tr>
        <th>Fecha registro</th>
        <th>Paciente</th>
        <th>Edad</th>
        <th>Teléfono</th>
        <th>Motivo</th>
        <th>Derivación</th>
        <th>Evaluación</th>
        <th>Padre</th>
        <th>Madre</th>
        <th>Estado OpenEMR</th>
        <th>Fecha subido</th>
        <th>Acción</th>
      </tr>
    </thead>

    <tbody>
      <?php while($row = $result->fetch_assoc()): ?>
        <tr>
          <td><?php echo htmlspecialchars($row['fecha_registro']); ?></td>

          <td>
            <?php echo htmlspecialchars($row['nombres']); ?>
            <?php if ((int)$row['es_menor'] === 1): ?>
              <div class="small">Menor de edad</div>
            <?php endif; ?>
          </td>

          <td><?php echo htmlspecialchars($row['edad']); ?></td>
          <td><?php echo htmlspecialchars($row['telefono']); ?></td>
          <td><?php echo nl2br(htmlspecialchars($row['motivo_consulta'])); ?></td>
          <td><?php echo htmlspecialchars($row['derivacion']); ?></td>
          <td><?php echo htmlspecialchars($row['evaluacion']); ?></td>

          <td>
            <?php if ((int)$row['es_menor'] === 1): ?>
              <?php echo htmlspecialchars($row['padre_nombre']); ?><br>
              <span class="small"><?php echo htmlspecialchars($row['padre_telefono']); ?></span>
            <?php else: ?>
              <span class="small">—</span>
            <?php endif; ?>
          </td>

          <td>
            <?php if ((int)$row['es_menor'] === 1): ?>
              <?php echo htmlspecialchars($row['madre_nombre']); ?><br>
              <span class="small"><?php echo htmlspecialchars($row['madre_telefono']); ?></span>
            <?php else: ?>
              <span class="small">—</span>
            <?php endif; ?>
          </td>

          <td>
            <?php if ((int)$row['subido_openemr'] === 1): ?>
              <span class="ok">Subido</span>
            <?php else: ?>
              <span class="pend">Pendiente</span>
            <?php endif; ?>
          </td>

          <td>
            <?php echo $row['fecha_subido'] ? htmlspecialchars($row['fecha_subido']) : "<span class='small'>—</span>"; ?>
          </td>

          <td>
            <?php if ((int)$row['subido_openemr'] === 1): ?>

              <form method="POST" action="marcar.php" style="margin-bottom:8px;">
                <input type="hidden" name="id" value="<?php echo (int)$row['id']; ?>">
                <input type="hidden" name="valor" value="0">
                <button class="btnundo" type="submit">Desmarcar</button>
              </form>

              <form method="POST" action="eliminar.php"
                    onsubmit="return confirm('¿Eliminar este registro? Esta acción no se puede deshacer.');">
                <input type="hidden" name="id" value="<?php echo (int)$row['id']; ?>">
                <button class="btndel" type="submit">Eliminar</button>
              </form>

            <?php else: ?>

              <form method="POST" action="marcar.php">
                <input type="hidden" name="id" value="<?php echo (int)$row['id']; ?>">
                <input type="hidden" name="valor" value="1">
                <button class="btnok" type="submit">Marcar como subido</button>
              </form>

            <?php endif; ?>
          </td>
        </tr>
      <?php endwhile; ?>
    </tbody>
  </table>
</div>

</body>
</html> 