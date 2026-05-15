<?php
$config = require __DIR__ . '/../config.local.php';

$conexion = new mysqli(
    $config['db_host'],
    $config['db_user'],
    $config['db_pass'],
    $config['db_name']
);
if ($conexion->connect_error) { die("Error de conexión: " . $conexion->connect_error); }

$id = isset($_POST['id']) ? (int)$_POST['id'] : 0;
$valor = (isset($_POST['valor']) && $_POST['valor'] === "1") ? 1 : 0;

if ($id > 0) {
  if ($valor === 1) {
    $stmt = $conexion->prepare("UPDATE registros_pacientes SET subido_openemr=1, fecha_subido=NOW() WHERE id=?");
  } else {
    $stmt = $conexion->prepare("UPDATE registros_pacientes SET subido_openemr=0, fecha_subido=NULL WHERE id=?");
  }
  $stmt->bind_param("i", $id);
  $stmt->execute();
}

header("Location: index.php");
exit;