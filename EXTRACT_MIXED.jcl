//EXTRACT  JOB (ACCT),'EXTRACT MIXED NUMCPT',CLASS=A,MSGCLASS=X,
//             NOTIFY=&SYSUID
//*
//* Extract records where NUMCPT has both negative and positive AMOUNTs.
//*
//* *** ADJUST TO MATCH YOUR LAYOUT ***
//*   NUMCPT : POS  1-10, CH  (account number, character)
//*   AMOUNT : POS 11-22, ZD  (signed zoned decimal, 12 digits)
//*   LRECL  : 80, RECFM=FB
//*
//*------------------------------------------------------------
//* STEP01 - One record per NUMCPT having at least 1 neg amount
//*------------------------------------------------------------
//STEP01   EXEC PGM=SORT
//SYSPRINT DD  SYSOUT=*
//SYSOUT   DD  SYSOUT=*
//SORTIN   DD  DSN=MY.PDS(MEMBER),DISP=SHR
//SORTOUT  DD  DSN=&&TEMPNEG,
//             DISP=(NEW,PASS),
//             SPACE=(TRK,(5,2),RLSE),
//             RECFM=FB,LRECL=10
//SYSIN    DD  *
  SORT FIELDS=(1,10,CH,A)
  INCLUDE COND=(11,12,ZD,LT,0)
  SUM FIELDS=NONE
  OUTREC FIELDS=(1,10)
/*
//*------------------------------------------------------------
//* STEP02 - One record per NUMCPT having at least 1 pos amount
//*------------------------------------------------------------
//STEP02   EXEC PGM=SORT
//SYSPRINT DD  SYSOUT=*
//SYSOUT   DD  SYSOUT=*
//SORTIN   DD  DSN=MY.PDS(MEMBER),DISP=SHR
//SORTOUT  DD  DSN=&&TEMPPOS,
//             DISP=(NEW,PASS),
//             SPACE=(TRK,(5,2),RLSE),
//             RECFM=FB,LRECL=10
//SYSIN    DD  *
  SORT FIELDS=(1,10,CH,A)
  INCLUDE COND=(11,12,ZD,GT,0)
  SUM FIELDS=NONE
  OUTREC FIELDS=(1,10)
/*
//*------------------------------------------------------------
//* STEP03 - Intersect: NUMCPTs present in BOTH temp files
//*   TEMPNEG and TEMPPOS are already sorted - use SORTED flag
//*------------------------------------------------------------
//STEP03   EXEC PGM=SORT
//SYSPRINT DD  SYSOUT=*
//SYSOUT   DD  SYSOUT=*
//SORTJNF1 DD  DSN=&&TEMPNEG,DISP=(OLD,DELETE)
//SORTJNF2 DD  DSN=&&TEMPPOS,DISP=(OLD,DELETE)
//SORTOUT  DD  DSN=&&TEMPBOTH,
//             DISP=(NEW,PASS),
//             SPACE=(TRK,(5,2),RLSE),
//             RECFM=FB,LRECL=10
//SYSIN    DD  *
  JOINKEYS F1=SORTJNF1,FIELDS=(1,10,A),SORTED
  JOINKEYS F2=SORTJNF2,FIELDS=(1,10,A),SORTED
  REFORMAT FIELDS=(F1:1,10)
/*
//*------------------------------------------------------------
//* STEP04 - Extract full original records for qualifying NUMCPTs
//*   Default JOINKEYS behaviour (no JOIN stmt) = PAIRED only
//*   F2 (TEMPBOTH) is pre-sorted; F1 (original) is sorted by DFSORT
//*------------------------------------------------------------
//STEP04   EXEC PGM=SORT
//SYSPRINT DD  SYSOUT=*
//SYSOUT   DD  SYSOUT=*
//SORTJNF1 DD  DSN=MY.PDS(MEMBER),DISP=SHR
//SORTJNF2 DD  DSN=&&TEMPBOTH,DISP=(OLD,DELETE)
//SORTOUT  DD  DSN=MY.OUTPUT.MIXED,
//             DISP=(NEW,CATLG,DELETE),
//             SPACE=(TRK,(10,5),RLSE),
//             RECFM=FB,LRECL=80,
//             BLKSIZE=27920
//SYSIN    DD  *
  JOINKEYS F1=SORTJNF1,FIELDS=(1,10,A)
  JOINKEYS F2=SORTJNF2,FIELDS=(1,10,A),SORTED
  REFORMAT FIELDS=(F1:1,80)
/*
