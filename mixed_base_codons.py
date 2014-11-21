#!/usr/bin/env python


#This file is part of DNApy. DNApy is a DNA editor written purely in python. 
#The program is intended to be an intuitive, fully featured, 
#extendible, editor for molecular and synthetic biology.  
#Enjoy!
#
#Copyright (C) 2014  Martin Engqvist | 
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#LICENSE:
#This file is part of DNApy.
#
#DNApy is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License, or
#(at your option) any later version.
# 
#DNApy is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Library General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software Foundation,
#Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#Get source code at: https://github.com/0b0bby0/DNApy
#

from copy import deepcopy
import dna
import re
	
	
#TODO 
#clean up code
#make code run faster

def getinput():
	###This is where I decide which AA I want
	DesiredAA = [];
	AllNaturalAA = ['F','L','S','Y','C','W','P','H','E','R','I','M','T','N','K','V','A','D','Q','G','*'];
	AA = 'x'
	table = raw_input('Input a number to indicate which codon table to use (standard is 1): ')
	if table is not int:
		table = 1
	while AA != '':
		AA = raw_input('Input single AA in single letter code. If done, press enter: ')
		AA = AA.upper()	
		if AA == '':
			pass	
		elif AA in AllNaturalAA:	
			DesiredAA.append(AA)	
		else:
			print('This is not a valid AA')
	DesiredAA = sorted(list(set(DesiredAA))) #condense list to what is unique
	#print(DesiredAA)
	return DesiredAA, table
	


class AmbigousCodon:
	'''
	Class that holds methods and values for computing the ambiguous codon for a list of amino acids.
	Required input is a list of desired amino acids in single letter code and 
	an integer that determines the codon table to use.
	
	The algorithm works as follows:
	A list of amino acids (as single letter code) is passed to the algorithm.
	All possible regular codons for those amino acids are looked up and returned as a list of lists -> get_triplets()
	All nucleotides for first, second and third position extracted into seperate lists while retaining list structure -> sumupcodons()
	Separately, for pos 1, 2 and 3, a degenerate nucleotide is found that matches at least one nucleotide in each lists -> commonNuc()
	These are concatenated and represents the first degenerate triplet
	The degenerate triplet is converted back to real codons xxxxx()
	translate to amino acids and check against what you wanted in the first place xxxxxxxx()

	Add more !!!!!!!!
	'''
	def __init__(self, input, table):
		self.setTable(table)
		
		#input can be either a three-nucleotide string or a list of amino acids
		if len(input) == 3 and type(input) == str: #if string i.e. an ambiguous codon
			input = input.upper()
			self.evaluateTriplet(input)
		elif type(input) == list: #if list, i.e. a list of amino acids to evaluate
			input = [s.upper() for s in input]
			self.setTarget(input)
		else:
			raise ValueError, 'The input is not valid'
		return

		
	######## Public methods intended for user interaction #########
	def getTarget(self):
		'''
		Retrieves a list of the target amino acids.
		'''
		return self.target
		
	def getOfftarget(self):
		'''
		Retrieves a list of the off-target amino acids.
		'''
		return self.offtarget
		
	def getPossible(self):
		'''
		Retrieves a list of amino acids still possible without further off-targets.
		'''
		return self.possible
		
	def getTriplet(self):
		'''
		Retrieves the ambiguous codon.
		'''
		return self.triplet	
		
	def getTable(self):
		'''
		Retrieves which genetic code was used.
		'''
		return self.table
		
	################################################################


	
	######## Methods NOT intended for direct user interaction ######
	def sumupcodons(self, DesiredCodons):
		'''
		Takes a list of regular codon lists and does two things; first it splits them up based on the first, second and third position of the triplet,
		then it checks which nucleotide (ambiguous allowed) that matches at least one of the nucleotides from each amino acid.	
		
		Example input, where alanine, cysteine and tyrosine are desired is: [['GCT', 'GCC', 'GCA', 'GCG'], ['TGT', 'TGC'], ['TAT', 'TAC']]
		The objective is to keep the list structure but to make three separate list where each 
		holds all the unique nucleotides for either the first, second or third base of the codons.
		The correct output for the first position would be: [['G'], ['T'], ['T']],
		for the second [['C'], ['G'], ['A']],
		and for the third [['T', 'C', 'A', 'G'], ['T', 'C'], ['T', 'C']].
		These lists can then be passed on to another function for finding a nucleotide that matches at least one of the nucleotides from each amino acid.	
		'''
		allcodon1 = []
		allcodon2 = []
		allcodon3 = []
		for entry in DesiredCodons:
			codon1 = []
			codon2 = []
			codon3 = []
			for codon in entry: #splits up the codons of each AA into triplets
				if codon[0] not in codon1:
					codon1.extend(codon[0]) #Takes first base in the triplet
				if codon[1] not in codon2:
					codon2.extend(codon[1]) #Takes the second base in triplet
				if codon[2] not in codon3:
					codon3.extend(codon[2]) #Takes third base in triplet
			allcodon1.append(codon1) #Adds up all the first bases
			allcodon2.append(codon2) #Adds up all the second bases
			allcodon3.append(codon3) #Adds up all the third bases
		return (allcodon1, allcodon2, allcodon3)



	def chosenvsresulting(self, DesiredAA, AAlist): 
		"""
		Function for checking a list vs another to find which are present in both and which are not.
		"""
		TargetAA = []
		OffTargetAA = []
		for entry in AAlist:
			if any(entry in s for s in DesiredAA):	
				TargetAA.append(entry)	
			else:
				OffTargetAA.append(entry)
		return OffTargetAA
	
	
	def flatten_codon_list(self, codon_list):
		output = []
		for pos in codon_list:
			output_len = len(output)
			if isinstance(pos[0], str):
				if output_len == 0:
					output.append([pos])
				else:
					for o in range(output_len):
						output[o].append(pos)
					
			elif isinstance(pos[0], list):
				if output_len == 0:
					for p in pos:
						output.append([p])
				else:
					output.extend(deepcopy(output * (len(pos)-1)))
					for i in range(len(pos)):
						for j in range(output_len):
							output[j+i*output_len].append(pos[i])
		return output

		
	def find_degenerate(self, AA_list):
		'''
		
		'''
		
		#get all codons for chosen amino acids
		regular_triplets = [dna.GetCodons(aa, table=self.table, separate=True) for aa in AA_list]
		
		#some of the codons are list of lists (happens when the amino acid has codons at different parts of the codon circle)
		#I need to flatten this into separate lists with which go on further
		regular_triplets = self.flatten_codon_list(regular_triplets)

		best_triplet = None #for storing best degenerate triplet
		best_offtarget = None #for storing the off-target AA of the best triplet
		best_score = None #for storing the length of the off-target list
		
		for codon_list in regular_triplets:
			#get all nucleotides for first, second and third position while retaining list structure		
			first, second, third = self.sumupcodons(codon_list) 
			
			#check which degenerate nucleotide can be used to find at least one match in each of the lists
			possible_triplets = dna.combine([dna.commonNuc(first), dna.commonNuc(second), dna.commonNuc(third)])
			
			#now go through them and see which is best
			for triplet in possible_triplets:
				#convert the triplet back to a list of real codons 
				Realcodons = dna.combine([dna.UnAmb(triplet[0]), dna.UnAmb(triplet[1]), dna.UnAmb(triplet[2])]) #condense the different codons for position 1, 2, and 3 to a list of triplets
			
				#Check which AA these codons code for
				ResultingAA = [dna.Translate(codon, table=self.table) for codon in Realcodons]

				#compare which amino acids were desired with the ones resulting from the degenerate codon
				offtarget = self.chosenvsresulting(AA_list, ResultingAA)
				offtarget = sorted(list(set(offtarget))) #condense list to what is unique
				
				if len(offtarget) < best_score or best_score == None:
					best_triplet = triplet
					best_offtarget = offtarget
					best_score = len(best_offtarget)
		
		return best_triplet, best_offtarget

	
	def next_steps(self):
		"""
		Function for finding which other amino acids can be selected without introducing 
		further (more in number) off-target ones.
		"""

		possibleAA = []
		targetAA = self.getTarget()
		unusedAA = self.chosenvsresulting(targetAA, list('FLSYCWPHERIMTNKVADQG*'))
		
		if len(unusedAA)>0:
			for AA in unusedAA:
				temptargetAA = targetAA[:]
				temptargetAA.append(AA)
				triplet, offtarget = self.find_degenerate(temptargetAA)
				if len(offtarget) <= len(self.getOfftarget()):
					possibleAA.append(AA)
		return sorted(possibleAA)


	def evaluateTriplet(self, amb_codon):
		
		m = re.match('^[GATCRYWSMKHBVDN]{3}$', amb_codon)
		assert m != None, 'Error, the codon %s is not valid' % amb_codon
		
		self.target = [dna.Translate(s, self.getTable()) for s in dna.UnAmb(amb_codon)]
		self.setTriplet(amb_codon) #the input ambigous codon
		self.setOfftarget([]) #no offtargets

		#see which other can be added without further off-target
		possible = self.next_steps()
		self.setPossible(possible)
		
	def setTarget(self, AA_list):
		for s in AA_list:
			assert s in 'FLSYCWPHERIMTNKVADQG*'
		self.target = AA_list
		
		#compute the triplet and the off-target AA
		triplet, offtarget = self.find_degenerate(self.getTarget())
		self.setTriplet(triplet)
		self.setOfftarget(offtarget)

		#see which other can be added without further off-target
		possible = self.next_steps()
		self.setPossible(possible)
	
	def setOfftarget(self, AA_list):
		self.offtarget = AA_list
	
	def setPossible(self, AA_list):
		self.possible = AA_list
	
	def setTriplet(self, triplet_string):
		self.triplet = triplet_string
		
	def setTable(self, table):
		self.table = table
	
	################################################################		

	
		
if __name__ == '__main__':
	AA, table = getinput()
	codon_object = AmbigousCodon(AA, table)
	print("mixed base codon: %s" % codon_object.getTriplet())
	print("target AA: %s" % codon_object.getTarget())
	print("off-target AA: %s" % codon_object.getOfftarget())
	print("AA that can be added w/o off-targets: %s" % codon_object.getPossible())
