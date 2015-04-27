from PyQt4 import QtGui, QtCore
import colors

class PopulateReductionTable(object):
	
	self = None
	
	def __init__(cls, self):

		cls.self = self
		_bigTableData = self.bigTableData
		cls.clearTable()

		[nbr_row, nbr_col] = _bigTableData.shape
		
		for r in range(nbr_row):
			
			if (_bigTableData[r,2] is not None):
				self.ui.reductionTable.insertRow(r)
			elif (_bigTableData[r,0] == None) and (_bigTableData[r,1] == None):
				break
			else:
				self.ui.reductionTable.insertRow(r)

			for c in range(2):
				_obj = _bigTableData[r,c]
				if c==1:
					col=6
				else:
					col=0

				if _obj == None:
					_obj_config = _bigTableData[r,2]
					if (_obj_config is None):
						_item = QtGui.QTableWidgetItem('')
						self.ui.reductionTable.setItem(r,col,_item)
					else:
						if c == 0:
							_data_run_number = _obj_config.data_sets
							_isOk = self.isPeakBackSelectionOkFromConfig(_obj_config, type='data')
							_item = QtGui.QTableWidgetItem(_data_run_number)
							_brush = QtGui.QBrush()
							if _isOk:
								_brush.setColor(colors.VALUE_OK)
							else:
								_brush.setColor(colors.VALUE_BAD)
							_item.setForeground(_brush)
							self.ui.reductionTable.setItem(r,0,_item)						
						else:
							_norm_run_number = _obj_config.norm_sets
							_isOk = self.isPeakBackSelectionOkFromConfig(_obj_config, type='norm')
							if _isOk:
								_brush.setColor(colors.VALUE_OK)
							else:
								_brush.setColor(colors.VALUE_BAD)
							_item = QtGui.QTableWidgetItem(_norm_run_number)
							_item.setForeground(_brush)
							self.ui.reductionTable.setItem(r,6,_item)						
				else:
					_run_number = _obj.active_data.run_number
					_item = QtGui.QTableWidgetItem(_run_number)
					if c==0:
						_isOk = self.isPeakBackSelectionOkFromNXSdata(_obj.active_data)
						cls.addMetadata(r, _obj)
					else:
						_isOk = self.isPeakBackSelectionOkFromNXSdata(_obj.active_data)
					if _isOk:
						_brush.setColor(colors.VALUE_OK)
					else:
						_brush.setColor(colors.VALUE_BAD)
					_item.setForeground(_brush)
					self.ui.reductionTable.setItem(r,col,_item)
						
	def clearTable(cls):
		cls.self.ui.reductionTable.clearContents()
		nbrRow = cls.self.ui.reductionTable.rowCount()
		if nbrRow > 0:
			for _row in range(nbrRow):
				cls.self.ui.reductionTable.removeRow(0)
				
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


