USE shopping;

CREATE TABLE IF NOT EXISTS Parcels (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id VARCHAR(255) NOT NULL,
        platform_id INT NOT NULL,
        status VARCHAR(255) NOT NULL,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY (order_id)
);

CREATE TABLE IF NOT EXISTS Subscriptions (
        sub_id INT AUTO_INCREMENT PRIMARY KEY,
        order_id VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        discord_id VARCHAR(255),
        platform_id INT NOT NULL,
        sub_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT email_or_dc CHECK (email IS NOT NULL OR discord_id IS NOT NULL),
        FOREIGN KEY (order_id) REFERENCES Parcels (order_id),
        UNIQUE (email, discord_id, order_id, platform_id)
);

CREATE TABLE IF NOT EXISTS Platforms (
        platform_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL
);

CREATE INDEX idx_order_id ON Parcels (order_id);



