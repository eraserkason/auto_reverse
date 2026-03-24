CREATE DATABASE IF NOT EXISTS `auto_reverse`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'auto_reverse'@'127.0.0.1'
  IDENTIFIED BY 'auto_reverse_pwd';

CREATE USER IF NOT EXISTS 'auto_reverse'@'localhost'
  IDENTIFIED BY 'auto_reverse_pwd';

GRANT ALL PRIVILEGES ON `auto_reverse`.* TO 'auto_reverse'@'127.0.0.1';
GRANT ALL PRIVILEGES ON `auto_reverse`.* TO 'auto_reverse'@'localhost';

FLUSH PRIVILEGES;
