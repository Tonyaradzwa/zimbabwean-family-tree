-- Individuals
INSERT INTO individuals (id, name, gender, birth_date) VALUES
  (1, 'Tendai', 'male', '1975-04-12'),
  (2, 'Rufaro', 'female', '1978-11-03'),
  (3, 'Chenai', 'female', '2001-07-20'),
  (4, 'Robert', 'male', '2004-02-15'),
  (5, 'Chipo', 'female', '1980-09-13'),
  (6, 'Blessing', 'male', '2010-06-09'),
  (7, 'Patricia', 'female', '2008-01-18');

-- Marriages
INSERT INTO marriages (id, partner1_id, partner2_id, date) VALUES
  (1, 1, 2, '2000-06-17'), -- Tendai & Rufaro married
  (2, 4, 5, '2025-08-10'); -- Robert & Chipo married

-- Parent-Child Relationships
INSERT INTO relationships (id, parent_id, child_id, type) VALUES
  (1, 1, 3, 'biological'),  -- Tendai -> Chenai
  (2, 2, 3, 'biological'),  -- Rufaro -> Chenai
  (3, 1, 4, 'biological'),  -- Tendai -> Robert
  (4, 2, 4, 'biological'),  -- Rufaro -> Robert
  (5, 4, 6, 'biological'),  -- Robert -> Blessing
  (6, 5, 6, 'biological'),  -- Chipo -> Blessing
  (7, 4, 7, 'biological'),  -- Robert -> Patricia
  (8, 5, 7, 'biological');  -- Chipo -> Patricia