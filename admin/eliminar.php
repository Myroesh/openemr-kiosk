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

if ($id > 0) {
  $stmt = $conexion->prepare("DELETE FROM registros_pacientes WHERE id=?");
  $stmt->bind_param("i", $id);
  $stmt->execute();
}

header("Location: index.php");
exit;