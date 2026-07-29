-- schema.sql
-- Database creation script for College Online Voting System

CREATE DATABASE IF NOT EXISTS college_voting;
USE college_voting;

-- 1. Table for Student Voters
CREATE TABLE IF NOT EXISTS voters (
    voter_id VARCHAR(50) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL
);

-- 2. Table for Candidates (Participants)
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id VARCHAR(50) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    degree VARCHAR(100) NOT NULL,
    qualification VARCHAR(255) NOT NULL,
    achievements TEXT NOT NULL,
    manifesto TEXT NOT NULL,
    image_url VARCHAR(255) DEFAULT '',
    position VARCHAR(50) NOT NULL -- 'President', 'Vice President', 'General Secretary', 'Sports Secretary'
);

-- 3. Table for cast votes (enforces single vote per position per voter)
CREATE TABLE IF NOT EXISTS votes (
    voter_id VARCHAR(50) NOT NULL,
    position VARCHAR(50) NOT NULL,
    candidate_id VARCHAR(50) NOT NULL,
    vote_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (voter_id, position),
    FOREIGN KEY (voter_id) REFERENCES voters(voter_id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
);

-- ===================================================
-- INSERTING INITIAL TEST DATA (Voters & Candidates)
-- ===================================================

-- Clear existing data if re-running
DELETE FROM votes;
DELETE FROM candidates;
DELETE FROM voters;

-- Insert Mock Voters (Students)
-- In production, passwords should be hashed. For development, we use plain text for simplicity.
INSERT INTO voters (voter_id, password, name, department) VALUES
('STU001', 'password123', 'David Miller', 'Computer Science'),
('STU002', 'password123', 'Emily Watson', 'Electronics Engineering'),
('STU003', 'password123', 'Sanjay Kumar', 'Mechanical Engineering'),
('STU004', 'password123', 'Aisha Rahman', 'Bio-Technology'),
('STU005', 'password123', 'Carlos Garcia', 'Information Technology');

-- Insert Mock Candidates (Participants)
INSERT INTO candidates (candidate_id, password, name, degree, qualification, achievements, manifesto, image_url, position) VALUES
-- President candidates
('PRES01', 'pass123', 'Jonathan Hughes', 'B.Tech CS, 3rd Year', 'Class Representative, GPA 3.9', 
 'Organized the annual national college hackathon, lead organizer of the environment club, active debate society mentor.', 
 'I promise to advocate for 24/7 library access, upgrade computer lab infrastructures, and establish a transparent student budget tracker.', 
 '', 'President'),

('PRES02', 'pass123', 'Priya Sharma', 'B.Sc Economics, 3rd Year', 'President of Debating Society, Sports Captain', 
 'Successfully petitioned for girls hostel security upgrades, organized corporate internship job fairs, represented college in national MUN.', 
 'My manifesto focuses on introducing mental wellness programs, campus-wide recycling, and establishing an entrepreneurial incubator cell.', 
 '', 'President'),

-- Vice President candidates
('VP01', 'pass123', 'Marcus Aurelius', 'B.Tech IT, 2nd Year', 'Secretary of Robotics Club, Event Coordinator', 
 'Co-organized the tech-fest tech exhibition, designed the college companion mobile app, active sports council member.', 
 'I will push for digital student ID card integrations, expand campus Wi-Fi bandwidth, and host monthly micro-innovation challenges.', 
 '', 'Vice President'),

('VP02', 'pass123', 'Sofia Rodriguez', 'B.Sc Mathematics, 2nd Year', 'General Secretary, Mathematics Association', 
 'Conducted peer-to-peer tutoring workshops for 1st-year students, coordinated inter-college math olympiad.', 
 'I pledge to secure subsidized student travel passes, increase funding for non-technical societies, and clean the sports arena.', 
 '', 'Vice President'),

-- Department Secretary candidates
('SEC01', 'pass123', 'Liam Carter', 'B.Tech CS, 2nd Year', 'Core member of Web Development Cell', 
 'Designed the departmental newsletter website, active volunteer at open source development community.', 
 'I will coordinate weekly coding contests, push for student-mentor guidance programs, and organize guest lectures from tech leaders.', 
 '', 'General Secretary'),

('SEC02', 'pass123', 'Neha Patel', 'B.Tech Biotech, 2nd Year', 'Class Coordinator, Cult-fest Organizer', 
 'Spearheaded department laboratory upgrades drive, organized cultural performances at the college foundation day.', 
 'I am dedicated to organizing regular industrial lab visits, expanding research seminar sessions, and bridging peer connection gaps.', 
 '', 'General Secretary');

-- 4. Table for Election Settings (Admin Controls)
CREATE TABLE IF NOT EXISTS election_settings (
    id INT PRIMARY KEY,
    election_status VARCHAR(20) NOT NULL DEFAULT 'STOPPED'
);

DELETE FROM election_settings;
INSERT INTO election_settings (id, election_status) VALUES (1, 'STOPPED');
