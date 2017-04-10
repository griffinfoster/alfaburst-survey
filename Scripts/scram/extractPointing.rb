#!/usr/local/bin/ruby

# extractPointings.rb
# extract the pointing data from scramdumps
#
# Usage: getPointings.rb [options]
#     -h  --help                           Display this usage information

require "getoptlong"

def printUsage(progName)
  puts <<-EOF
Usage: #{progName} [options]
    -h  --help                           Display this usage information
    -m  --mjd <mjd>                      MJD of the pointings
  EOF
end


opts = GetoptLong.new(
  [ "--help",       "-h", GetoptLong::NO_ARGUMENT ]
)

# constants
SCRAMDumpDir = "/data/serendip6"
#SCRAMDumpDir = "/home/artemis/scramtest"
TempDir = "/home/artemis"

opts.each do |opt, arg|
  case opt
    when "--help"
      printUsage($PROGRAM_NAME)
      exit
  end
end

Dir.glob("#{SCRAMDumpDir}/scramdump.142*.gz.at_ucb") do |scramDumpGZ|
	puts "Working on #{scramDumpGZ}"
	
	# copy file to temp directory
	cmd = "cp -a #{scramDumpGZ} #{TempDir}/"
	puts cmd
	%x[#{cmd}]

	# build path to file in temp directory
	scramDumpGZTemp = TempDir + "/" + File.basename(scramDumpGZ)
	# gunzip with any suffix, preserving the name, forcing
	cmd = "gunzip --force --name --suffix .at_ucb #{scramDumpGZTemp}"
	puts cmd
	%x[#{cmd}]

	fileList = scramDumpGZTemp.split("/").last.split(".")
	scramDump = TempDir + "/#{fileList[0]}.#{fileList[1]}"
	pointingOutput = scramDump + ".out"
	cmd = "s6_observatory -nodb -stdout -infile #{scramDump} 2>&1 > /dev/null | grep RA0 | uniq > #{pointingOutput}"
	puts cmd
	%x[#{cmd}]

	# remove the copied scram dump
	cmd = "rm -f #{scramDump}"
	puts cmd
	%x[#{cmd}]
end

