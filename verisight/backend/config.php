<?php
$host = "127.0.0.1";
$dbname = "verisight";
$user = "root";
$pass = "";
try {
  $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $user, $pass);
  $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
  die("DB connection failed: " . $e->getMessage());
}
?>
