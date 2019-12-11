#!/usr/bin/perl
# File:       mktosh.pl
# Author:     Jesper Eskilson <jojo@virtutech.se>
# Created:    20 May 2001

use Config;

@inputs = @ARGV;

$hash="#";

%mkvars= ();

$uname_s=`uname -s`;

if ($uname_s =~ m/cygwin/i and $Config{archname} =~ m/Win32/i) {
  print STDERR "mktosh.pl is being run with a Win32 Perl, using cygpath to convert Cygwin paths to native form.\n";
  $do_cygpath_conv=1;
} else {
  $do_cygpath_conv=0;
}

sub to_native_form
{
  $file = $_[0];
  if ($do_cygpath_conv) {
    $cygpath= `cygpath -w '$file'`;
    chomp $cygpath;
    return $cygpath;
  } else {
    return $file;
  }
}

sub get_mkvars {
  local *INPUTFILE;
  my $enabled;

  $enabled=1;
  $file = to_native_form($_[0]);

  if (not open(INPUTFILE, "< $file")) {
    print STDERR "...skipping $file: $!\n";
    return 0;
  }

  print STDERR "parsing: $file\n";

 LOOP: while (<INPUTFILE>) {
    my $line = $_;
    if ($line =~ /^$hash\s*enable mktosh\s*$/) {
      $enabled=1;
      next LOOP;
    }
    if ($line =~ /^$hash\s*disable mktosh\s*$/) {
      $enabled=0;
      next LOOP;
    }
    if ($enabled and ($line =~ /^\s*-?include\s*(.*)\s*$/)) {
      $ifile = $1;
      #print STDERR ">>>$ifile<<<\n";
      $ifile =~ s/\$\((.*?)\)/$ENV{$1}/g;
      $ifile = to_native_form($ifile);
      if (-f $ifile) {
	  # print STDERR "...following makefile included from $file: $ifile\n";
	  get_mkvars($ifile);
      } else {
	  #print STDERR "NO SUCH FILE: >>>$ifile<<<\n";
      }
    }
    if ($enabled and ($line =~ /^\s*(\w+)\s*([\+:]?=)\s*(.*)\s*$/)) {
      $mkvars{$1}=1;
    }
  }

  close(INPUTFILE);
}

# host-flags.* can check for $(MKTOSH)=yes if they need to know
# if they're parsed by configure or not. Needed to workaround problem
# with $(LDFLAGS) being passed to $(CC).
print "MKTOSH=yes\n";

# print "\$(warning \$(SHELL))\n";

for $file (@inputs) {
  print "include $file\n";
  get_mkvars($file);
}

@MKVARLIST=();

for $var (sort keys %mkvars) {
  push @MKVARLIST, $var;
}

# The makefile has a target per variable. We could just have one target,
# but then make wouldn't be able to give any good error messages.

print ".PHONY: ";
for $var (@MKVARLIST) {
  print "var_$var ";
}
print "\n";

print "all: ";
for $var (@MKVARLIST) {
  print "var_$var ";
}
print "\n";

for $var (@MKVARLIST) {
  print "$var:=\$(subst ','\\'\\\\\\'\\'',\$($var))\n";
  print "var_$var: \n";
  print "\t\@echo $var=\\''\$($var)'\\'\n";
  print "\n";
}
