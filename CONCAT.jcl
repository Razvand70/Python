//CONCAT   JOB (ACCT),'CONCATENATE FILES',CLASS=A,MSGCLASS=X,
//             NOTIFY=&SYSUID
//*
//* IBM JCL to concatenate two input files into one output file
//* using IEBGENER utility
//*
//STEP01   EXEC PGM=IEBGENER
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  DUMMY
//SYSUT2   DD  DSN=MY.OUTPUT.FILE,
//             DISP=(NEW,CATLG,DELETE),
//             SPACE=(TRK,(5,2),RLSE),
//             RECFM=FB,
//             LRECL=80,
//             BLKSIZE=800
//SYSUT1   DD  DSN=MY.INPUT.FILE1,
//             DISP=SHR
//         DD  DSN=MY.INPUT.FILE2,
//             DISP=SHR
