/*
ANT728 (Team Pandas) CRSP request
  Firms : PERMCOs in crsp_permcos.csv (NY Fed CRSP-FRB link, active 2022-12-31)
  Dates : 2022-01-01 to 2023-12-31
  Source: WRDS legacy CRSP daily (SIZ format): crsp.dsf, dsenames, dsedelist, dsi
Outputs (CSV, in this folder):
  crsp_daily_2022_2023.csv   one row per PERMNO-date, all share classes, names merged as of date,
                             delisting fields filled on the row whose date = DLSTDT
  crsp_delistings.csv        every delisting record for the sample PERMNOs (any date >= 2022)
  crsp_market_vwretd.csv     CRSP value-weighted market return by date
Dates are pulled as text (a native date load through ODBC has returned missing values).
*/

	clear
	set more off
	capture log close
	log using pull_crsp_run.log, replace text

	local d0 '2022-01-01'
	local d1 '2023-12-31'

/* PERMCO list -> SQL IN list */

	import delimited using crsp_permcos.csv, clear varnames(1)
	capture confirm variable permco
	if _rc {
		rename `: word 1 of `: ds'' permco
	}
	destring permco, replace force
	drop if missing(permco)
	duplicates drop permco, force
	di as result "PERMCOs: " _N
	levelsof permco, local(pcs) separate(,) clean
	save permco_list, replace

/* Daily stock file with names as of each date */

	local q "SELECT a.permno, a.permco, CAST(a.date AS TEXT) AS date, a.ret, a.retx, a.prc, a.shrout, a.vol, n.ticker, n.comnam, n.shrcd, n.exchcd FROM crsp.dsf a LEFT JOIN crsp.dsenames n ON a.permno = n.permno AND a.date BETWEEN n.namedt AND COALESCE(n.nameendt, DATE '9999-12-31') WHERE a.permco IN (`pcs') AND a.date BETWEEN `d0' AND `d1' ORDER BY a.permno, a.date"

	clear
	odbc load, exec("`q'") dsn("wrds-pgdata-64")
	gen ddate = date(date, "YMD")
	format ddate %tdCCYY-NN-DD
	drop date
	rename ddate date
	isid permno date
	save dsf_tmp, replace

/* Delistings for the sample PERMNOs */

	local q "SELECT d.permno, d.permco, CAST(d.dlstdt AS TEXT) AS dlstdt, d.dlstcd, d.dlret, d.dlretx, CAST(d.dlpdt AS TEXT) AS dlpdt, d.dlamt, d.nwperm, d.nwcomp FROM crsp.dsedelist d WHERE d.permco IN (`pcs') AND d.dlstdt >= `d0' ORDER BY d.permno"

	clear
	odbc load, exec("`q'") dsn("wrds-pgdata-64")
	foreach v in dlstdt dlpdt {
		gen t_`v' = date(`v', "YMD")
		drop `v'
		rename t_`v' `v'
		format `v' %tdCCYY-NN-DD
	}
	order permno permco dlstdt dlstcd dlret dlretx dlpdt dlamt nwperm nwcomp
	export delimited using crsp_delistings.csv, replace
	keep permno dlstdt dlstcd dlret
	gen date = dlstdt
	format date %tdCCYY-NN-DD
	isid permno
	save dlst_tmp, replace

	use dsf_tmp, clear
	merge 1:1 permno date using dlst_tmp
	* delistings whose DLSTDT has no daily row in the window (kept only in crsp_delistings.csv)
	di as result "Delistings with no matching daily row:"
	list permno dlstdt dlstcd if _merge == 2, clean noobs
	drop if _merge == 2
	drop _merge
	order permno permco date ticker comnam shrcd exchcd ret retx prc shrout vol dlstdt dlstcd dlret
	sort permno date
	export delimited using crsp_daily_2022_2023.csv, replace

	* summary for the README / log
	di as result "Daily rows: " _N
	egen tag_pno = tag(permno)
	egen tag_pco = tag(permco)
	count if tag_pno
	count if tag_pco
	tab shrcd if tag_pno, missing
	drop tag_*

	* PERMCOs in the list with no daily data in the window
	preserve
	keep permco
	duplicates drop
	merge 1:1 permco using permco_list
	di as result "PERMCOs without CRSP daily rows in window:"
	list permco if _merge == 2, clean noobs
	restore

/* Market return */

	local q "SELECT CAST(date AS TEXT) AS date, vwretd, vwretx, ewretd FROM crsp.dsi WHERE date BETWEEN `d0' AND `d1' ORDER BY date"

	clear
	odbc load, exec("`q'") dsn("wrds-pgdata-64")
	gen ddate = date(date, "YMD")
	format ddate %tdCCYY-NN-DD
	drop date
	rename ddate date
	order date
	isid date
	export delimited using crsp_market_vwretd.csv, replace
	di as result "Market days: " _N

	erase dsf_tmp.dta
	erase dlst_tmp.dta
	erase permco_list.dta
	log close
