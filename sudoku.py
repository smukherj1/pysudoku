import json
import sys
import time
import os

DEBUG = 4
debug_fout = None
if DEBUG > 0:
	debug_fout = open('debug_output.txt', 'w')

def info(*args):
	msg = 'Info: ' + (' '.join(args))
	print msg
	return
	
def error(*args):
	msg = 'Error: ' + (' '.join(args))
	print msg
	return
	
def debug(msg, level=1):
	if DEBUG >= level:
		msg = 'Debug: ' + msg
		debug_fout.write(msg + '\n')
	return
	
def is_valid(val):
	result = True
	result = result and (type(val) is int)
	result = result and (val >= 1) and (val <= 9)
	return result
	

class placer_element_t:
	def __init__(self, i, j):
		assert(i >= 0 and i < 9)
		assert(j >= 0 and j < 9)
		self.i = i
		self.j = j
		self.current_val = -1
		self.vals = []
		self.used_vals = set()
		self.locked_vals = []
		
	def push_lock(self, i, j):
		self.locked_vals.append([i, j])
		return
		
	def clear_lock(self):
		self.locked_vals.clear()
		return
	
	def pop(self):
		popped = self.vals.pop()
		self.used_vals.add(popped)
		return popped
		
	def __repr__(self):
		return "'PE val: %d (%d, %d) %s'"%(self.current_val, self.i + 1, self.j + 1, str([val for val in self.vals]))

class sudoku_table_t:
	def __init__(self, int_2d_array):
		self.rows = 9
		self.cols = 9
		assert(type(int_2d_array) is list)
		assert(len(int_2d_array) == self.rows)
		
		self.constraints = [[] for i in range(self.rows)]
		
		for i in range(self.rows):
			assert(type(int_2d_array[i]) is list)
			assert(len(int_2d_array) == self.cols)
			for j in range(self.cols):
				self.constraints[i].append(set())
				val = int_2d_array[i][j]
				assert(is_valid(val) or val == -1)
		
		self.grid = int_2d_array
		return
		
	def next_placer_element(self):
		pe_list = []
		for i in range(self.rows):
			for j in range(self.cols):
				val = self.grid[i][j]
				if not is_valid(val):
					pe = placer_element_t(i, j)
					pe.vals = list(self.constraints[i][j])
					pe_list.append(pe)
		pe_list = sorted(pe_list, key = lambda pe : len(pe.vals))
		if pe_list:
			pe = pe_list[0]
			debug("Next PE (%d, %d) %d vals"%(pe.i + 1, pe.j + 1, len(pe.vals)))
			return pe
		else:
			return 
			
	def commit_pe(self, pe, val):
		debug(">>>Commit %d at (%d, %d)"%(val, pe.i + 1, pe.j + 1))
		pe.current_val = val
		assert(self.commit_if_legal(pe.i, pe.j, val))
		return
		
	def commit_if_legal(self, i, j, val):
		legal = False
		if val in self.legal_vals(i, j):
			legal = True
			self.grid[i][j] = val
		return legal
		
	def undo_pe(self, pe):
		if pe.current_val == -1:
			return
		debug("<<<Undo %d at (%d, %d)"%(pe.current_val, pe.i + 1, pe.j + 1))
		pe.current_val = -1
		self.grid[pe.i][pe.j] = -1
		for i_j_pair in pe.locked_vals:
			i = i_j_pair[0]
			j = i_j_pair[1]
			self.grid[i][j] = -1
		return 
		
	def legal_vals(self, i, j):
		val_set = set()
		for icol in range(self.cols):
			if icol == j:
				continue
			val = self.grid[i][icol]
			if is_valid(val):
				val_set.add(val)
		for irow in range(self.rows):
			if irow == i:
				continue
			val = self.grid[irow][j]
			if is_valid(val):
				val_set.add(val)
		
		row_box = int(i / 3)
		col_box = int(j / 3)
		for irow in range(row_box * 3, row_box * 3 + 3):
			for icol in range(col_box * 3, col_box * 3 + 3):
				if irow == i and icol == j:
					continue
				val_set.add(self.grid[irow][icol])
				
		legal_vals = set(range(1, 10)) - val_set
		return legal_vals
		
	def propagate_constraints(self, print_errors=False):
		result = 0
		num_failed = 0
		for i in range(self.rows):
			for j in range(self.cols):
				old_constraints = self.constraints[i][j]
				self.constraints[i][j] = self.legal_vals(i, j)
				if (not self.constraints[i][j]) and (not is_valid(self.grid[i][j])):
					result = -1
					if print_errors:
						error("No legal values at row %d, col %d"%(i + 1, j + 1))
					debug("      No legal values at row %d, col %d"%(i + 1, j + 1), level=4)
					num_failed += 1
				elif result != -1:
					if old_constraints != self.constraints[i][j]:
						result += 1
		if print_errors and (result == -1):
			error("Constraint propagation failed")
		if num_failed > 0:
			debug("      No legal values at %d locations"%num_failed, level=3)
		return result
		
	def dump(self, stage=''):
		pad_stars = 30 - len(stage)
		if pad_stars < 0:
			pad_stars = ''
		else:
			pad_stars = '*' * pad_stars
		if stage:
			info(pad_stars + ' Begin ' + stage + ' ' + pad_stars)
		
		info(' --------- --------- ---------')
		for i in range(self.rows):
			row_str = '|'
			for j in range(self.cols):
				val = self.grid[i][j]
				if val == -1:
					row_str += '   '
				else:
					row_str += ' %d '%val
				if ((j + 1) % 3) == 0:
					row_str += '|'
			info(row_str)
			if ((i + 1) % 3) == 0:
				info(' --------- --------- ---------')
					
			
		if stage:
			info(pad_stars + '* End ' + stage + ' *' + pad_stars)
		return
		
	def solved(self):
		for i in range(self.rows):
			for j in range(self.cols):
				val = self.grid[i][j]
				if not is_valid(val):
					return False
		return True
		
	def num_unsolved(self):
		count = 0
		for i in range(self.rows):
			for j in range(self.cols):
				val = self.grid[i][j]
				if not is_valid(val):
					count += 1
		return count
		
def l_lock_constrainted_cells(table, pe):
	num_locked = 0
	for i in range(table.rows):
		for j in range(table.cols):
			if len(table.constraints[i][j]) == 1 and not(is_valid(table.grid[i][j])):
				locked_val = [x for x in table.constraints[i][j]][0]			
				if table.commit_if_legal(i, j, locked_val):
					debug("         Locking (%d, %d) to %d"%(i + 1, j + 1, locked_val), level=3)
					num_locked += 1
					if [i, j] not in pe.locked_vals:
						pe.push_lock(i, j)
	if num_locked > 0:
		debug("         Locked %d cells"%num_locked, level=2)
	return
		
def l_refresh_until_converged(table, pe):
	debug("   Refreshing until converged for PE (%d, %d)"%(pe.i + 1, pe.j + 1), level=2)
	result = True
	iterations = 1
	num_cells_changed = table.propagate_constraints()
	while num_cells_changed > 0:
		debug("      Round %d with %d cells changed"%(iterations, num_cells_changed), level=2)
		l_lock_constrainted_cells(table, pe)
		num_cells_changed = table.propagate_constraints()
		iterations += 1
	
	assert(num_cells_changed <= 0)
	result = (num_cells_changed == 0)
	if not result:
		debug("      Refresh failed!", level=2)

	return result
	
def l_run_auto_placer(table):
	if table.propagate_constraints(print_errors=True) == -1:
		return
	info('%d empty locations remain after initial constraint propagation'%table.num_unsolved())
	info('Running the pure flexibility placement engine')
	iteration = 0
	pe_list = [table.next_placer_element()]
	assert(pe_list[0] != None or table.solved())
	while pe_list and (not table.solved()):
		iteration += 1
		debug('Iteration %d '%iteration + str(pe_list))

		pe = pe_list.pop()
		table.undo_pe(pe)
		if not pe.vals:
			continue

		pe_list.append(pe)
		next_val = pe.pop()
		if next_val in table.legal_vals(pe.i, pe.j):
			table.commit_pe(pe, next_val)
			if l_refresh_until_converged(table, pe):
				next_pe = table.next_placer_element()
				if next_pe != None:
					pe_list.append(next_pe)
	info('Placer performed %d iterations'%iteration)
	return
		
def l_do_placement(table):
	print ''
	start = time.time()
	info('Beginning placement operations')
	info('Found %d empty locations'%table.num_unsolved())
	l_run_auto_placer(table)
	
	table.dump('after placement')
	if table.solved():
		info('Placement was successful')
	else:
		error('Placement was unsuccessful')
	end = time.time()
	info('Placement operations ending. Elapsed time is %.0f seconds'%(end - start))
	return
		
def l_load_table():
	info('Beginning placement preparation')
	
	if len(sys.argv) != 2:
		error('Expected exactly one command line argument giving the name of the sudoku file in jSON format')
		exit(1)
	
	sudoku_filename = sys.argv[1]
	if not os.path.isfile(sudoku_filename):
		error('Could not open sudoku filename %s'%sudoku_filename)
		exit(1)
	
	f_in = open(sudoku_filename)
	int_2d_array = json.load(f_in)
	table = sudoku_table_t(int_2d_array)
	table.dump(stage = 'initial board')
	info('Placement preparation operations ending')
	print ''
	return table
	
		
def main():
	table = l_load_table()
	l_do_placement(table)
	return
	
main()
	