# MicrobeCensus - estimation of average genome size from shotgun sequence data
# Copyright (C) 2013-2015 Stephen Nayfach
# Freely distributed under the GNU General Public License (GPLv3)

"""
Usage:
    python search_reads.py <threads>
    
    <threads>: number of threads to use

Description: perform translated search of simulated reads against database of marker genes
    do for all library listed in ../data/reads
    libraries should be formatted as "genome_name"-reads.fa
    search results are written to ../data/search/read_length
    search results are formatted as "genome_name".m8

"""

# Libraries
import sys, os, tempfile, subprocess, platform
from training import *
from shutil import copy

# Arguments
threads = int(sys.argv[1])

# Filepaths to input/output data
main_dir     = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
gene_fam_dir = os.path.join(main_dir, 'training/input/gene_fams')
reads_dir    = os.path.join(main_dir, 'training/intermediate/reads')
search_dir   = os.path.join(main_dir, 'training/intermediate/search')
seqs_path    = os.path.join(main_dir, 'training/intermediate/seqs.fa')
diamonddb_path = os.path.join(main_dir, 'training/intermediate/seqs')
diamond_path = '/usr/bin/diamond'#os.path.join(main_dir, 'microbe_census/bin/diamond')


# Build database if necessary
if not os.path.isfile(diamonddb_path):
    print 'RAPsearch2 database does not exist. Creating...'
    # cat sequences together in tempfile
    f_out = open(seqs_path, 'w')
    gene_fams = os.listdir(gene_fam_dir)
    if len(gene_fams) == 0: sys.exit('No gene families found in %s' % gene_fam_dir)
    for gene_fam in gene_fams:
        if gene_fam[-7:] != '.faa.gz': sys.exit('Unknown file extension: %s. Fasta files must have .faa.gz extension' % gene_fam[-7:])
        for line in gzip.open(os.path.join(gene_fam_dir, gene_fam)):
            f_out.write(line)
    f_out.close()
    # create rapsearch database
    command = "%s --in %s --db %s" % (diamond_path, seqs_path, diamonddb_path)
    p = subprocess.Popen(command, shell=True)
    p.wait()
    # delete seqs
    os.remove(seqs_path)

diamonddb_path = os.path.join(main_dir, 'training/intermediate/seqs.dmnd')
args_list = []
for read_length in os.listdir(reads_dir):
    src_dir  = os.path.join(reads_dir, read_length)
    dest_dir = os.path.join(search_dir, read_length)
    if not os.path.isdir(dest_dir): os.mkdir(dest_dir) # create outdir if not exists
    for reads_file in os.listdir(src_dir):
        if reads_file[-9:] == '-reads.fa': # check file extension
            genome_name = reads_file[0:-9]
            reads_path = os.path.join(src_dir, reads_file)
            out_name = os.path.join(dest_dir, genome_name + '.m8')
            diamond_args = [diamond_path,
                            'blastx',
                            '-p',
                            str(threads),
                            '--db',
                            diamonddb_path,
                            '--query',
                            reads_path,
                            '--out',
                            out_name,
                            '--evalue',
                            '1.0',
                            '-k','100','--outfmt','6','qseqid','sseqid','pident','length','mismatch','gapopen','qstart','qend','sstart','send','evalue','bitscore'
                            ]
            print (diamond_args)
            with Popen(diamond_args, stdout=PIPE, stderr = PIPE, bufsize=1, universal_newlines=True) as p:
                for line in p.stdout:
                    print (line, end='')
            if p.returncode != 0:
                raise CalledProcessError(p.returncode, p.args)

# Print arguments
print "Threads to use: %s" % threads
print "Read lengths: %s" % os.listdir(reads_dir)
print "Number of libraries to search: %s" % len(args_list)
print "Output directory: %s" % search_dir

# Clean up
for read_length in os.listdir(search_dir):
    lib_dir = os.path.join(search_dir, read_length)
    for file in os.listdir(lib_dir):
        path_file = os.path.join(lib_dir, file)
        if file[-3:] != '.m8': os.remove(path_file)


