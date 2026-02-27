-- Insert Individuals
INSERT INTO individuals (id, name, gender, birth_date) VALUES
  (1, 'Tendai', 'male', '1975-04-12'),
  (2, 'Rufaro', 'female', '1978-11-03'),
  (3, 'Chenai', 'female', '2001-07-20'),
  (4, 'Robert', 'male', '2004-02-15'),
  (5, 'Chipo', 'female', '1980-09-13'),
  (6, 'Blessing', 'male', '2010-06-09'),
  (7, 'Patricia', 'female', '2008-01-18');

-- Reset sequence (if you use SERIAL/auto-increment in Postgres)
SELECT setval(pg_get_serial_sequence('individuals', 'id'), (SELECT MAX(id) FROM individuals));

-- Insert Marriages
INSERT INTO marriages (id, partner1_id, partner2_id, date) VALUES
  (1, 1, 2, '2000-06-17'),
  (2, 4, 5, '2025-08-10');

SELECT setval(pg_get_serial_sequence('marriages', 'id'), (SELECT MAX(id) FROM marriages));

-- Insert Relationships
INSERT INTO relationships (id, parent_id, child_id, type) VALUES
  (1, 1, 3, 'biological'),
  (2, 2, 3, 'biological'),
  (3, 1, 4, 'biological'),
  (4, 2, 4, 'biological'),
  (5, 4, 6, 'biological'),
  (6, 5, 6, 'biological'),
  (7, 4, 7, 'biological'),
  (8, 5, 7, 'biological');

SELECT setval(pg_get_serial_sequence('relationships', 'id'), (SELECT MAX(id) FROM relationships));