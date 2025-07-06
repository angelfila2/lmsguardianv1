-- Drop tables if they already exist (in reverse dependency order)
DROP TABLE IF EXISTS scraped_contents;

DROP TABLE IF EXISTS reports;

DROP TABLE IF EXISTS scraper_sessions;

DROP TABLE IF EXISTS modules;

DROP TABLE IF EXISTS unit_coordinators;

-- UnitCoordinator Table
CREATE TABLE unit_coordinators (
    uc_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- Module Table
CREATE TABLE modules (
    module_id SERIAL PRIMARY KEY,
    uc_id INT NOT NULL,
    module_name VARCHAR(255) NOT NULL,
    teaching_period VARCHAR(50),
    semester VARCHAR(50),
    module_description TEXT,
    unit_code VARCHAR(50),
    CONSTRAINT fk_uc FOREIGN KEY (uc_id) REFERENCES unit_coordinators (uc_id)
);

-- ScraperSession Table
CREATE TABLE scraper_sessions (
    session_id SERIAL PRIMARY KEY,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    completion_status VARCHAR(50),
    error_log TEXT
);

-- Report Table
CREATE TABLE reports (
    report_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL,
    module_id INT NOT NULL,
    report_type VARCHAR(100),
    report_content TEXT,
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES scraper_sessions (session_id),
    CONSTRAINT fk_module_report FOREIGN KEY (module_id) REFERENCES modules (module_id)
);

-- ScrapedContent Table (with risk_score and risk_category)
CREATE TABLE scraped_contents (
    scraped_id SERIAL PRIMARY KEY,
    module_id INT NOT NULL,
    session_id INT NOT NULL,
    scraped_at TIMESTAMP,
    url_link TEXT,
    risk_score FLOAT,
    risk_category VARCHAR(100),
    content_location TEXT,
    is_paywall BOOLEAN DEFAULT FALSE,
    apa7 TEXT,
    CONSTRAINT fk_module_scraped FOREIGN KEY (module_id) REFERENCES modules (module_id),
    CONSTRAINT fk_session_scraped FOREIGN KEY (session_id) REFERENCES scraper_sessions (session_id)
);

-- Insert Unit Coordinator
INSERT INTO
    unit_coordinators (full_name, email)
VALUES ('Peter Col', 'XXXX@gmail.com')
RETURNING
    uc_id;

-- Insert Modules linked to that UC
INSERT INTO
    modules (
        uc_id,
        module_name,
        teaching_period,
        semester,
        module_description,
        unit_code
    )
VALUES (
        1,
        'ICT302 IT Professional Practice Project',
        'TMA',
        '2025',
        'This team-based university unit provides students with the opportunity to solve real-world problems across various domains. Projects will be carefully selected, and groups formed to best leverage the knowledge and skills acquired from each student’s respective major(s). Recognizing the interdisciplinary nature of the project, students will collaborate with team members from different IT majors to solve complex problems effectively. Emphasis will be placed on project management, interdisciplinary teamwork, professional communication with clients and stakeholders, and the delivery of relevant project outcomes. Furthermore, students will have the opportunity to engage with industry professionals, allowing them to gain insights into IT professional practices. These industry engagement opportunities aim to support students professional development and enhance their readiness for a successful career in the IT industry.',
        'ICT302'
    ),
    (
        1,
        'BSC203',
        'TMA',
        '2025',
        'This team-based university unit provides students with the opportunity to solve real-world problems across various domains. Projects will be carefully selected, and groups formed to best leverage the knowledge and skills acquired from each student’s respective major(s). Recognizing the interdisciplinary nature of the project, students will collaborate with team members from different IT majors to solve complex problems effectively. Emphasis will be placed on project management, interdisciplinary teamwork, professional communication with clients and stakeholders, and the delivery of relevant project outcomes. Furthermore, students will have the opportunity to engage with industry professionals, allowing them to gain insights into IT professional practices. These industry engagement opportunities aim to support students professional development and enhance their readiness for a successful career in the IT industry.',
        'BSC203'
    );