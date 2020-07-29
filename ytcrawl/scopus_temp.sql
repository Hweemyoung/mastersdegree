-- phpMyAdmin SQL Dump
-- version 4.5.4.1deb2ubuntu2.1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Jul 29, 2020 at 06:10 PM
-- Server version: 5.7.30-0ubuntu0.16.04.1
-- PHP Version: 7.0.33-0ubuntu0.16.04.15

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `ytcrawl0`
--

-- --------------------------------------------------------

--
-- Table structure for table `scopus_temp`
--

CREATE TABLE `scopus_temp` (
  `Authors` text,
  `Author(s) ID` text,
  `Title` varchar(1000) DEFAULT NULL,
  `Year` year(4) DEFAULT NULL,
  `Source title` varchar(150) DEFAULT NULL,
  `Volume` varchar(15) DEFAULT NULL,
  `Issue` varchar(15) DEFAULT NULL,
  `Art. No.` varchar(15) DEFAULT NULL,
  `Page start` varchar(6) DEFAULT NULL,
  `Page end` varchar(6) DEFAULT NULL,
  `Page count` varchar(3) DEFAULT NULL,
  `Cited by` varchar(5) DEFAULT NULL,
  `DOI` varchar(100) DEFAULT NULL,
  `Link` varchar(300) DEFAULT NULL,
  `Affiliations` text,
  `Authors with affiliations` text,
  `Abstract` text,
  `Author Keywords` varchar(1000) DEFAULT NULL,
  `Index Keywords` text,
  `Molecular Sequence Numbers` text,
  `Chemicals/CAS` varchar(1000) DEFAULT NULL,
  `Tradenames` varchar(100) DEFAULT NULL,
  `Manufacturers` varchar(100) DEFAULT NULL,
  `Funding Details` varchar(1000) DEFAULT NULL,
  `Funding Text 1` text,
  `Funding Text 2` text,
  `Funding Text 3` text,
  `References` text,
  `Correspondence Address` varchar(1000) DEFAULT NULL,
  `Editors` varchar(10) DEFAULT NULL,
  `Sponsors` varchar(10) DEFAULT NULL,
  `Publisher` varchar(100) DEFAULT NULL,
  `Conference name` varchar(50) DEFAULT NULL,
  `Conference date` varchar(10) DEFAULT NULL,
  `Conference location` varchar(1000) DEFAULT NULL,
  `Conference code` varchar(10) DEFAULT NULL,
  `ISSN` varchar(20) DEFAULT NULL,
  `ISBN` varchar(20) DEFAULT NULL,
  `CODEN` varchar(10) DEFAULT NULL,
  `PubMed ID` varchar(20) DEFAULT NULL,
  `Language of Original Document` varchar(15) DEFAULT NULL,
  `Document Type` varchar(30) DEFAULT NULL,
  `Publication Stage` varchar(10) DEFAULT NULL,
  `Access Type` enum('nan','Open Access') DEFAULT NULL,
  `EID` varchar(30) DEFAULT NULL,
  `Redirection` varchar(150) DEFAULT NULL,
  `PDF` varchar(150) DEFAULT NULL,
  `idx` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `scopus_temp`
--
ALTER TABLE `scopus_temp`
  ADD PRIMARY KEY (`idx`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `scopus_temp`
--
ALTER TABLE `scopus_temp`
  MODIFY `idx` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
