#!/usr/bin/perl
# sample.pl -- Parse instrument CSV log and compute statistics
# PEEKDOCS_TEST_MARKER

use strict;
use warnings;
use List::Util qw(sum min max);

my $filename = $ARGV[0] || 'sensor_log.csv';

open(my $fh, '<', $filename) or die "Cannot open $filename: $!\n";

my @readings;
my $header = <$fh>;  # skip header

while (my $line = <$fh>) {
    chomp $line;
    my ($timestamp, $channel, $value) = split /,/, $line;
    next unless defined $value && $value =~ /^[\d.eE+-]+$/;
    push @readings, $value;
}
close $fh;

die "No valid readings found\n" unless @readings;

my $n     = scalar @readings;
my $mean  = sum(@readings) / $n;
my $min   = min(@readings);
my $max   = max(@readings);
my $range = $max - $min;

my $variance = sum(map { ($_ - $mean) ** 2 } @readings) / ($n - 1);
my $stddev   = sqrt($variance);

printf "Samples: %d\n",       $n;
printf "Mean:    %.4f\n",      $mean;
printf "Std Dev: %.4f\n",      $stddev;
printf "Range:   %.4f (%.4f - %.4f)\n", $range, $min, $max;
