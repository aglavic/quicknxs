from PyQt4 import QtGui, QtCore
import colors

class PopulateReductionTable(object):
	
	self = None
	
	def __init__(cls, self):
		cls.self = self
		_bigTableData = self.bigTableData

		[nbr_col, nbr_row] = _bigTableData.shape
		
		for r in range(nbr_row):
			if (_bigTableData[0,r] == None) and (_bigTableData[1,r] == None):
				return
			else:
				self.ui.reductionTable.insertRow(r)

			for c in range(2):
				_obj = _bigTableData[r,c]
				if c==1:
					c=6

				if _obj == None:
					_item = QtGui.QTableWidgetItem('')
					self.ui.reductionTable.setItem(r,c,_item)
				else:
					_run_number = _obj.active_data.run_number
					_item = QtGui.QTableWidgetItem(_run_number)
					_item.setForeground(QtGui.QColor(13,24,241))
					self.ui.reductionTable.setItem(r,c,_item)
					if c==0:
						cls.addMetadata(r, _obj)
						

	def addMetadata(cls, row, obj):
		_color = colors.METADATA_CELL_COLOR
		_active_data = obj.active_data

		incident_angle = _active_data.incident_angle
		_item_angle = QtGui.QTableWidgetItem(incident_angle)
		_item_angle.setFlags(QtCore.Qt.ItemIsEnabled)
		_item_angle.setForeground(_color)
		cls.self.ui.reductionTable.setItem(row, 1, _item_angle)
		
		[from_lambda, to_lambda] = _active_data.lambda_range
		_item_from_l = QtGui.QTableWidgetItem(str(from_lambda))
		_item_from_l.setForeground(_color)
		_item_from_l.setFlags(QtCore.Qt.ItemIsEnabled)
		cls.self.ui.reductionTable.setItem(row, 2, _item_from_l)
		_item_to_l = QtGui.QTableWidgetItem(str(to_lambda))
		_item_to_l.setForeground(_color)
		_item_to_l.setFlags(QtCore.Qt.ItemIsEnabled)
		cls.self.ui.reductionTable.setItem(row, 3, _item_to_l)

		[from_q, to_q] = _active_data.q_range
		_item_from_q = QtGui.QTableWidgetItem(str(from_q))
		_item_from_q.setForeground(_color)
		_item_from_q.setFlags(QtCore.Qt.ItemIsEnabled)
		cls.self.ui.reductionTable.setItem(row, 4, _item_from_q)
		_item_to_q = QtGui.QTableWidgetItem(str(to_q))
		_item_to_q.setForeground(_color)
		_item_to_q.setFlags(QtCore.Qt.ItemIsEnabled)
		cls.self.ui.reductionTable.setItem(row, 5, _item_to_q)


