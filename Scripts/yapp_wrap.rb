#!/usr/bin/ruby

# Wrapper around YAPP tools that takes into account skipping and processing
# ALFABURST buffers.
#
# Usage: yapp_wrap.rb [options]
#     -h  --help                            Display this usage information
#     -b  --buffer                          ID of buffer to be processed
#     -y  --yapp "<yapp-command>"           YAPP command

require "getoptlong"

def printUsage(progName)
  puts <<-EOF
Usage: #{progName} [options]
    -h  --help                           Display this usage information
    -b  --buffer                         ID of buffer to be processed
    -y  --yapp "<yapp-command>"          YAPP command
  EOF
end


opts = GetoptLong.new(
  [ "--help",       "-h", GetoptLong::NO_ARGUMENT ],
  [ "--buffer",     "-b", GetoptLong::REQUIRED_ARGUMENT ],
  [ "--yapp",       "-y", GetoptLong::REQUIRED_ARGUMENT ]
)

# buffer number
buffer = 0

# constants
ComputeNodeDataDir = "/data/Survey/Data"
NumSamples = 32768
SampTime = 0.000256     # seconds

yappCmd = ""

opts.each do |opt, arg|
  case opt
    when "--help"
      printUsage($PROGRAM_NAME)
      exit
    when "--buffer"
      # set the buffer number
      buffer = arg.to_i
    when "--yapp"
      # set YAPP command
      yappCmd = arg
  end
end

# compute skip time and proc time
skipTime = (buffer - 1) * NumSamples * SampTime
procTime = NumSamples * SampTime

yappTool = yappCmd.split[0]
yappOpts = yappCmd.split[1..-1].join(" ")

cmd = "#{yappTool} --skip #{skipTime} --proc #{procTime} #{yappOpts}"
puts cmd
%x[#{cmd}]

