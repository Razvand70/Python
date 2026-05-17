//CONCSORT JOB (ACCT),'CONCAT WITH SORT',CLASS=A,MSGCLASS=X,
//             NOTIFY=&SYSUID
//*
//* IBM JCL to concatenate two input files and sort the result
//* using DFSORT/ICETOOL utility
//*
//STEP01   EXEC PGM=SORT
//SYSPRINT DD  SYSOUT=*
//SYSOUT   DD  SYSOUT=*
//SORTIN   DD  DSN=MY.INPUT.FILE1,
//             DISP=SHR
//         DD  DSN=MY.INPUT.FILE2,
//             DISP=SHR
//SORTOUT  DD  DSN=MY.OUTPUT.SORTED,
//             DISP=(NEW,CATLG,DELETE),
//             SPACE=(TRK,(5,2),RLSE),
//             RECFM=FB,
//             LRECL=80,
//             BLKSIZE=800
//SYSIN    DD  *
  SORT FIELDS=COPY
/*
